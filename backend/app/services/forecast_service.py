"""
内示管理サービス - 実際のPDFフォーマット対応版
商品マスタ紐付けあり・なし両方に対応
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
    return _parse_honda_forecast(text)


def _parse_honda_forecast(text: str) -> dict:
    # 月ラベルを抽出（例: 26-04 → 2026-04）
    month_pattern = re.findall(r"\b(\d{2})-(\d{2})\b", text)
    month_labels = []
    seen = set()
    for yy, mm in month_pattern:
        year = 2000 + int(yy)
        label = f"{year}-{mm}"
        if label not in seen and 1 <= int(mm) <= 12:
            seen.add(label)
            month_labels.append(label)
    month_labels = month_labels[:6]

    items = _extract_items_from_text(text, month_labels)

    return {
        "customer": _find_customer(text),
        "forecast_month": month_labels[0] if month_labels else datetime.now().strftime("%Y-%m"),
        "month_labels": month_labels,
        "items": items,
        "raw_text": text[:2000],
        "total_items": len(items),
    }


def _extract_items_from_text(text: str, month_labels: list) -> list:
    items = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    part_no_pattern = re.compile(r"^([A-Z0-9]{4,}-[A-Z0-9]{2,}(?:\s*-\s*[A-Z0-9]+)*(?:\s*-\s*\d+)?(?:\s*-\s*\d+)?)")

    i = 0
    while i < len(lines):
        line = lines[i]
        m = part_no_pattern.match(line)
        if m:
            part_no = m.group(1).strip()
            name_match = re.search(r"([A-Z][A-Z,\(\)\s\-\.]{4,})", line)
            part_name = name_match.group(1).strip() if name_match else part_no

            block_nums = []
            j = i + 1
            while j < len(lines) and j < i + 60:
                next_line = lines[j].strip()
                if part_no_pattern.match(next_line) and j > i + 2:
                    break
                if re.match(r"^\d{1,6}$", next_line):
                    block_nums.append(("qty", int(next_line)))
                elif re.match(r"^[\d,]+\.\d{2}$", next_line):
                    block_nums.append(("price", next_line))
                elif re.match(r"^[\d,]{5,}$", next_line):
                    block_nums.append(("amount", next_line))
                j += 1

            qtys = [v for t, v in block_nums if t == "qty"]
            month_qtys = qtys[:6]
            while len(month_qtys) < 6:
                month_qtys.append(0)

            if any(q > 0 for q in month_qtys) and len(part_no) >= 5:
                items.append({
                    "part_no": part_no,
                    "sku": part_no,
                    "product_name": part_name,
                    "month_qtys": month_qtys,
                    "month_labels": month_labels[:6] if month_labels else [
                        (datetime.now() + relativedelta(months=k)).strftime("%Y-%m")
                        for k in range(6)
                    ],
                })
            i = j
        else:
            i += 1

    return items[:100]


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
                key = fi.product_id or fi.sku
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
