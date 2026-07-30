"""
内示管理サービス - 実際のPDFフォーマット完全対応版
PDFの構造: 全データが1行に連結されている
部番+カラー+単価群+合計数量+月別数量×6+部品名+金額群
"""
import re
import uuid
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import List
from sqlalchemy.orm import Session

from app.models.forecast import (
    ForecastOrder, ForecastItem, LeadTime, SafetyStock,
    AutoOrderProposal, AutoOrderProposalItem, ForecastStatus, ProposalStatus
)
from app.models.inventory import Inventory
from app.models.purchase_order import PurchaseOrder, POStatus
from app.models.product import Product

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


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
    """
    実際のPDFフォーマットを解析
    月ヘッダーが連結: "26-0426-0526-0626-0726-0826-09"
    データが1行に連結: "部番カラー単価群合計数量月別数量×6部品名金額群"
    """
    # 月ラベル抽出（連結形式: "26-0426-05..." → ["2026-04","2026-05"...]）
    month_block = re.search(r'((?:\d{2}-\d{2}){2,})', text)
    month_labels = []
    if month_block:
        raw = month_block.group(1)
        month_labels_raw = re.findall(r'\d{2}-\d{2}', raw)
        month_labels = [f"20{m}" for m in month_labels_raw[:6]]

    # デフォルト月ラベル（抽出失敗時）
    if not month_labels:
        month_labels = [
            (datetime.now() + relativedelta(months=i)).strftime("%Y-%m")
            for i in range(6)
        ]

    items = _extract_items(text, month_labels)

    return {
        "customer": _find_customer(text),
        "forecast_month": month_labels[0] if month_labels else datetime.now().strftime("%Y-%m"),
        "month_labels": month_labels,
        "items": items,
        "raw_text": text[:1000],
        "total_items": len(items),
    }


def _extract_items(text: str, month_labels: list) -> list:
    """
    部番+月別数量を抽出
    パターン: 部番 カラーコード 単価群 合計数量 月1 月2 月3 月4 月5 月6 部品名
    """
    # 部番パターン: 数字+英字で始まり、ハイフン区切り
    # カラーコード: K2AE00, K3AF03 等
    pattern = re.compile(
        r'(\d[A-Z]\d{3}-[A-Z0-9]{2,}(?:\s*-\s*[A-Z0-9]+)*(?:\s*-\s*\d+)?(?:\s*-\s*\d+)?)'
        r'\s*([A-Z]\d[A-Z]{2}\d{2})'      # カラーコード
        r'(?:\s+[\d,]+\.\d{2})*'           # 単価群（スキップ）
        r'\s+(\d{1,6})'                    # 合計数量
        r'\s+(\d{1,6})'                    # 月1
        r'\s+(\d{1,6})'                    # 月2
        r'\s+(\d{1,6})'                    # 月3
        r'\s+(\d{1,6})'                    # 月4
        r'\s+(\d{1,6})'                    # 月5
        r'\s+(\d{1,6})'                    # 月6
        r'\s*([A-Z][A-Z,\(\)\s\-\.A-Z]{3,30}?)'  # 部品名
        r'(?:\s+[\d,]+|\s*$)'              # 数値または行末
    )

    items = []
    seen = set()

    for m in pattern.finditer(text):
        part_no = m.group(1).strip()
        total_qty = int(m.group(3))
        month_qtys = [int(m.group(i)) for i in range(4, 10)]
        part_name = m.group(10).strip().rstrip(',').strip()

        # 重複除去
        if part_no in seen:
            continue
        seen.add(part_no)

        # 月別合計の検証（合計数量と大きく乖離する場合はスキップ）
        month_sum = sum(month_qtys)
        if total_qty > 0 and month_sum > 0 and abs(month_sum - total_qty) > total_qty * 0.5:
            continue

        items.append({
            "part_no": part_no,
            "sku": part_no,
            "product_name": part_name,
            "month_qtys": month_qtys,
            "month_labels": month_labels[:6],
            "total_qty": total_qty,
        })

    return items[:100]


def _find_customer(text: str) -> str:
    """取引先情報を抽出"""
    m = re.search(r'取引先[（(](\d+)[）)]', text)
    if m:
        return f"取引先コード: {m.group(1)}"
    return "（PDFから自動抽出）"


def calculate_order_proposals(db: Session, supplier_id: str, target_month: str) -> List[dict]:
    """
    発注数量 = 内示数量 - 現在庫数量 - 発注残数量 + 安全在庫係数
    商品マスタ紐付けあり・なし両方に対応
    """
    proposals = []
    forecast_items = db.query(ForecastItem).all()

    # 内示明細を集計（部番ベース）
    item_map = {}
    for fi in forecast_items:
        for i, label in enumerate([fi.month_1_label, fi.month_2_label, fi.month_3_label,
                                    fi.month_4_label, fi.month_5_label, fi.month_6_label]):
            if label == target_month:
                qty = getattr(fi, f"month_{i+1}_qty", 0) or 0
                if qty == 0:
                    continue
                key = fi.product_id or fi.sku or fi.product_name
                if key not in item_map:
                    item_map[key] = {
                        "product_id": fi.product_id,
                        "sku": fi.sku,
                        "product_name": fi.product_name,
                        "forecast_qty": 0,
                    }
                item_map[key]["forecast_qty"] += qty

    for key, item_data in item_map.items():
        forecast_qty = item_data["forecast_qty"]
        product_id = item_data["product_id"]
        sku = item_data["sku"]
        product_name = item_data["product_name"]

        if product_id:
            # 商品マスタ紐付きの場合
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                if supplier_id and product.supplier_id and product.supplier_id != supplier_id:
                    continue
                inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
                current_stock = inv.quantity if inv else 0
                pending_orders = db.query(PurchaseOrder).filter(
                    PurchaseOrder.supplier_id == supplier_id,
                    PurchaseOrder.status.in_([POStatus.ordered, POStatus.confirmed, POStatus.in_transit])
                ).all()
                pending_qty = sum(
                    item.quantity for po in pending_orders
                    for item in po.items if item.product_id == product_id
                )
                safety = db.query(SafetyStock).filter(SafetyStock.product_id == product_id).first()
                safety_qty = safety.safety_stock_qty if safety else 0
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
                    "linked": True,
                })
        else:
            # 商品マスタ未登録の場合（内示数量をそのまま発注数量に）
            proposals.append({
                "product_id": None,
                "product_name": product_name,
                "sku": sku,
                "forecast_qty": forecast_qty,
                "current_stock": 0,
                "pending_order_qty": 0,
                "safety_stock_qty": 0,
                "proposed_qty": forecast_qty,
                "unit_price": 0,
                "amount": 0,
                "unit": "個",
                "formula": f"{forecast_qty} - 0 - 0 + 0 = {forecast_qty}（商品マスタ未登録）",
                "linked": False,
            })

    return proposals


def create_proposal_from_calculation(db: Session, supplier_id: str, target_month: str, items: List[dict]) -> AutoOrderProposal:
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
        db.add(AutoOrderProposalItem(
            id=str(uuid.uuid4()),
            proposal_id=proposal.id,
            product_id=item.get("product_id"),
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
        ))

    proposal.total_amount = total
    db.commit()
    db.refresh(proposal)
    return proposal
