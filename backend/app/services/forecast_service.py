"""
内示管理サービス
- PDFから内示数量を抽出
- 自動発注数量計算: 発注数量 = 内示数量 - 現在庫 - 発注残 + 安全在庫
- 発注提案の生成
"""
import json
import re
import uuid
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.forecast import (
    ForecastOrder, ForecastItem, LeadTime, SafetyStock,
    AutoOrderProposal, AutoOrderProposalItem, ForecastStatus, ProposalStatus
)
from app.models.inventory import Inventory
from app.models.purchase_order import PurchaseOrder, POStatus
from app.models.product import Product
from app.models.company import Company

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ─── PDF内示データ抽出 ────────────────────────────────────────────────

def extract_forecast_from_pdf(file_path: str) -> dict:
    """PDFから内示データを抽出"""
    text = ""
    if PDF_AVAILABLE:
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        except Exception as e:
            print(f"PDF読み込みエラー: {e}")

    return _parse_forecast_text(text)

def _parse_forecast_text(text: str) -> dict:
    """テキストから内示データをパース"""
    result = {
        "customer": _find(r'(?:得意先|Customer|Bill\s*To)[:\s]+([^\n]+)', text, "（自動抽出）"),
        "forecast_month": _find(r'(\d{4}[-/年]\d{1,2})', text, datetime.now().strftime("%Y-%m")),
        "items": [],
        "raw_text": text[:1000],
    }

    # 月ラベルを抽出（例: 2026-08, 2026/09 など）
    month_labels = re.findall(r'(\d{4}[-/]\d{1,2})', text)
    month_labels = list(dict.fromkeys(month_labels))[:6]  # 重複除去・最大6ヶ月

    # 商品行を抽出（SKU + 数量パターン）
    item_patterns = [
        r'([A-Z]{2,}-\d{3})\s+([^\n]+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)',
        r'(SKU-\d+)\s+([^\n]+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)',
        r'([A-Za-z0-9\-]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)',
    ]

    items_found = []
    for pat in item_patterns:
        for m in re.finditer(pat, text, re.MULTILINE):
            groups = m.groups()
            if len(groups) >= 7:
                try:
                    qtys = [int(g) for g in groups[-6:]]
                    items_found.append({
                        "sku": groups[0].strip(),
                        "product_name": groups[1].strip() if len(groups) > 7 else groups[0].strip(),
                        "month_qtys": qtys,
                    })
                except Exception:
                    continue
        if items_found:
            break

    # 月ラベルを付与
    base_month = datetime.now()
    for item in items_found:
        labels = []
        for i in range(6):
            m = base_month + relativedelta(months=i)
            labels.append(m.strftime("%Y-%m"))
        item["month_labels"] = labels[:6]
        result["items"].append(item)

    # 抽出できなかった場合はサンプルデータ
    if not result["items"]:
        result["items"] = _generate_sample_items()

    return result

def _generate_sample_items() -> list:
    """PDF抽出失敗時のサンプル（手動修正用）"""
    base = datetime.now()
    labels = [(base + relativedelta(months=i)).strftime("%Y-%m") for i in range(6)]
    return [
        {"sku": "", "product_name": "（PDFから自動抽出できませんでした。手動で入力してください）",
         "month_qtys": [0, 0, 0, 0, 0, 0], "month_labels": labels}
    ]

def _find(pattern: str, text: str, default: str = "") -> str:
    m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else default

# ─── 自動発注数量計算 ─────────────────────────────────────────────────

def calculate_order_proposals(
    db: Session,
    supplier_id: str,
    target_month: str,  # "2026-08"
) -> List[dict]:
    """
    発注数量 = 内示数量 - 現在庫数量 - 発注残数量 + 安全在庫係数
    """
    proposals = []

    # 対象月の全内示を取得
    forecast_items = db.query(ForecastItem).all()

    # 商品ごとに集計
    product_forecasts = {}
    for fi in forecast_items:
        if not fi.product_id:
            continue
        # 対象月の内示数量を取得
        for i, label in enumerate([fi.month_1_label, fi.month_2_label, fi.month_3_label,
                                    fi.month_4_label, fi.month_5_label, fi.month_6_label]):
            if label == target_month:
                qty_attr = f"month_{i+1}_qty"
                qty = getattr(fi, qty_attr, 0) or 0
                if fi.product_id not in product_forecasts:
                    product_forecasts[fi.product_id] = 0
                product_forecasts[fi.product_id] += qty

    for product_id, forecast_qty in product_forecasts.items():
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product or product.supplier_id != supplier_id:
            continue

        # 現在庫数量
        inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
        current_stock = inv.quantity if inv else 0

        # 発注残数量（ordered/confirmed/in_transit の合計）
        pending_orders = db.query(PurchaseOrder).filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.status.in_([POStatus.ordered, POStatus.confirmed, POStatus.in_transit])
        ).all()
        pending_qty = 0
        for po in pending_orders:
            for item in po.items:
                if item.product_id == product_id:
                    pending_qty += item.quantity

        # 安全在庫係数
        safety = db.query(SafetyStock).filter(SafetyStock.product_id == product_id).first()
        safety_qty = safety.safety_stock_qty if safety else 0

        # 発注数量計算
        proposed_qty = max(0, forecast_qty - current_stock - pending_qty + safety_qty)

        proposals.append({
            "product_id": product_id,
            "product_name": product.product_name,
            "sku": product.sku,
            "forecast_qty": forecast_qty,
            "current_stock": current_stock,
            "pending_order_qty": pending_qty,
            "safety_stock_qty": safety_qty,
            "proposed_qty": proposed_qty,
            "unit_price": float(product.unit_price) if product.unit_price else 0,
            "amount": proposed_qty * float(product.unit_price) if product.unit_price else 0,
            "unit": product.unit,
            "formula": f"{forecast_qty} - {current_stock} - {pending_qty} + {safety_qty} = {proposed_qty}",
        })

    return proposals

def create_proposal_from_calculation(
    db: Session,
    supplier_id: str,
    target_month: str,
    items: List[dict],
) -> AutoOrderProposal:
    """計算結果から発注提案を作成"""
    proposal = AutoOrderProposal(
        id=str(uuid.uuid4()),
        supplier_id=supplier_id,
        proposal_date=date.today(),
        target_month=target_month,
        status=ProposalStatus.draft,
        currency="JPY",
    )
    db.add(proposal)
    db.flush()

    total = 0
    for item in items:
        if item.get("proposed_qty", 0) <= 0:
            continue
        amount = item.get("proposed_qty", 0) * item.get("unit_price", 0)
        total += amount
        pi = AutoOrderProposalItem(
            id=str(uuid.uuid4()),
            proposal_id=proposal.id,
            product_id=item["product_id"],
            product_name=item["product_name"],
            sku=item.get("sku", ""),
            forecast_qty=item.get("forecast_qty", 0),
            current_stock=item.get("current_stock", 0),
            pending_order_qty=item.get("pending_order_qty", 0),
            safety_stock_qty=item.get("safety_stock_qty", 0),
            proposed_qty=item.get("proposed_qty", 0),
            unit_price=item.get("unit_price", 0),
            amount=amount,
            unit=item.get("unit", "個"),
        )
        db.add(pi)

    proposal.total_amount = total
    db.commit()
    db.refresh(proposal)
    return proposal