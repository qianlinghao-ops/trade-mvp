"""
内示管理サービス - 実際のPDFフォーマット完全対応版 v4
上期・下期を完全分離処理
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


def _normalize_text(text: str) -> str:
    for _ in range(4):
        text = re.sub(r"(\d),(\d{3})\b", r"\1\2", text)
    return text


def _parse_forecast_text(text: str) -> dict:
    text_norm = _normalize_text(text)

    # ページ境界を検出（月ヘッダーの位置）
    page_boundaries = []
    for mb in re.finditer(r"((?:\d{2}-\d{2}){2,})", text_norm):
        raw = mb.group(1)
        labels_raw = re.findall(r"\d{2}-\d{2}", raw)
        labels = [f"20{m}" for m in labels_raw if 1 <= int(m.split("-")[1]) <= 12]
        if len(labels) >= 2:
            page_boundaries.append((mb.start(), labels[:6]))

    if not page_boundaries:
        page_boundaries = [(0, [(datetime.now() + relativedelta(months=i)).strftime("%Y-%m") for i in range(6)])]

    # 全ページを分割して処理
    all_items = []
    for idx, (boundary_pos, month_labels) in enumerate(page_boundaries):
        # このページの終端
        next_pos = page_boundaries[idx + 1][0] if idx + 1 < len(page_boundaries) else len(text_norm)
        page_text = text_norm[boundary_pos:next_pos]
        
        # このページの部番を抽出
        page_items = _extract_items_from_page(page_text, month_labels)
        all_items.extend(page_items)

    # 重複除去（同じ部番+月ラベルの組み合わせ）
    seen = set()
    unique_items = []
    for item in all_items:
        key = f"{item['part_no']}_{item['month_labels'][0] if item['month_labels'] else ''}"
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    first_month = page_boundaries[0][1][0] if page_boundaries else datetime.now().strftime("%Y-%m")
    all_month_sets = [pb[1] for pb in page_boundaries]

    print(f"ページ数: {len(page_boundaries)}, 抽出件数: {len(unique_items)}")
    for pb in page_boundaries:
        print(f"  月セット: {pb[1]}")

    return {
        "customer": _find_customer(text),
        "forecast_month": first_month,
        "month_labels": page_boundaries[0][1] if page_boundaries else [],
        "all_month_sets": all_month_sets,
        "items": unique_items,
        "raw_text": text[:1000],
        "total_items": len(unique_items),
    }


def _extract_items_from_page(page_text: str, month_labels: list) -> list:
    """1ページ分のテキストから部番と月別数量を抽出"""
    items = []
    seen_parts = set()

    for cc_match in re.finditer(r"([A-Z]\d[A-Z]{2}\d{2})", page_text):
        color = cc_match.group()
        cc_start = cc_match.start()
        cc_end = cc_match.end()

        before = page_text[max(0, cc_start - 100):cc_start]
        part_match = re.search(
            r"(\d{4,5}-[A-Z0-9]{2,}(?:\s*-\s*[A-Z0-9]+)*(?:\s*-\s*\d+)?(?:\s*-\s*\d+)?)\s*$",
            before
        )
        if not part_match:
            part_match = re.search(
                r"([A-Z]\d[A-Z0-9]{3}-[A-Z0-9]{2,}(?:\s*-\s*[A-Z0-9]+)*(?:\s*-\s*\d+)?(?:\s*-\s*\d+)?)\s*$",
                before
            )
        if not part_match:
            continue

        part_no = part_match.group(1).strip()
        if part_no in seen_parts:
            continue

        after = page_text[cc_end:cc_end + 600]
        after_no_prices = re.sub(r"\d+\.\d{2}", "", after)
        int_tokens = re.findall(r"(?<!\d)(\d{1,7})(?!\d)", after_no_prices)
        int_nums = [int(t) for t in int_tokens if int(t) <= 9999999]

        if len(int_nums) >= 7:
            total_qty = int_nums[0]
            month_qtys = int_nums[1:7]

            if any(q > 0 for q in month_qtys):
                # 部品名称を抽出
                name_match = re.search(
                    r"\d\s*([A-Z][A-Z,\(\)\s\-\.A-Z0-9]{3,50}?)(?:\s+\d|\s*$)",
                    after_no_prices
                )
                part_name = name_match.group(1).strip() if name_match else ""
                if len(part_name) < 4:
                    name_match2 = re.search(r"([A-Z][A-Z,\(\)\s\-\.]{3,50}?)\s+\d", after)
                    if name_match2:
                        part_name = name_match2.group(1).strip()

                items.append({
                    "part_no": part_no,
                    "sku": part_no,
                    "product_name": part_name,
                    "month_qtys": month_qtys,
                    "month_labels": month_labels[:6],
                    "total_qty": total_qty,
                })
                seen_parts.add(part_no)

    return items


def _find_customer(text: str) -> str:
    m = re.search(r"取引先[（(](\d+)[）)]", text)
    if m:
        return f"取引先コード: {m.group(1)}"
    return "（PDFから自動抽出）"


def calculate_order_proposals(db: Session, supplier_id: str, target_month: str) -> List[dict]:
    proposals = []
    forecast_items = db.query(ForecastItem).all()

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
