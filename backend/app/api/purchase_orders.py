from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem, POStatus
from app.models.inventory import Inventory, InventoryLog
import uuid
from datetime import datetime, date

router = APIRouter(prefix="/purchase-orders", tags=["purchase_orders"])

def _po_to_dict(po):
    return {"id": po.id, "po_number": po.po_number, "supplier_id": po.supplier_id, "supplier_name": po.supplier.company_name if po.supplier else "", "status": po.status, "order_date": po.order_date.isoformat() if po.order_date else None, "expected_date": po.expected_date.isoformat() if po.expected_date else None, "total_amount": float(po.total_amount) if po.total_amount else 0, "currency": po.currency, "payment_terms": po.payment_terms, "notes": po.notes, "created_at": po.created_at.isoformat() if po.created_at else None, "items": [{"id": i.id, "product_id": i.product_id, "product_name": i.product_name, "sku": i.sku, "quantity": i.quantity, "unit_price": float(i.unit_price) if i.unit_price else 0, "amount": float(i.amount) if i.amount else 0, "unit": i.unit} for i in po.items]}

@router.get("")
async def list_purchase_orders(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(PurchaseOrder)
    if status: q = q.filter(PurchaseOrder.status == status)
    orders = q.order_by(PurchaseOrder.created_at.desc()).all()
    return {"total": len(orders), "items": [_po_to_dict(o) for o in orders]}

@router.post("")
async def create_purchase_order(body: dict, db: Session = Depends(get_db)):
    count = db.query(PurchaseOrder).count()
    now_ym = datetime.now().strftime('%Y%m')
    po_number = body.get("po_number") or f"PO-{now_ym}-{count+1:04d}"
    po = PurchaseOrder(id=str(uuid.uuid4()), po_number=po_number, supplier_id=body.get("supplier_id",""), status=body.get("status", POStatus.draft), order_date=date.fromisoformat(body["order_date"]) if body.get("order_date") else date.today(), expected_date=date.fromisoformat(body["expected_date"]) if body.get("expected_date") else None, currency=body.get("currency","JPY"), payment_terms=body.get("payment_terms",""), notes=body.get("notes",""))
    db.add(po); db.flush()
    total = 0
    for item_data in body.get("items",[]):
        qty = int(item_data.get("quantity",1)); price = float(item_data.get("unit_price",0)); amount = qty * price; total += amount
        db.add(PurchaseOrderItem(id=str(uuid.uuid4()), purchase_order_id=po.id, product_id=item_data.get("product_id"), product_name=item_data.get("product_name",""), sku=item_data.get("sku",""), quantity=qty, unit_price=price, amount=amount, unit=item_data.get("unit","個")))
    po.total_amount = total; db.commit(); db.refresh(po)
    return _po_to_dict(po)

@router.get("/{po_id}")
async def get_purchase_order(po_id: str, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po: raise HTTPException(404, "発注書が見つかりません")
    return _po_to_dict(po)

@router.put("/{po_id}/status")
async def update_po_status(po_id: str, body: dict, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po: raise HTTPException(404, "発注書が見つかりません")
    new_status = body.get("status"); po.status = new_status; po.updated_at = datetime.utcnow()
    if new_status == POStatus.received:
        for item in po.items:
            if item.product_id:
                inv = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
                if inv:
                    inv.quantity += item.quantity; inv.updated_at = datetime.utcnow()
                    db.add(InventoryLog(id=str(uuid.uuid4()), inventory_id=inv.id, log_type="in", quantity_change=item.quantity, quantity_after=inv.quantity, reference_id=po.po_number, notes=f"発注書 {po.po_number} 入荷"))
    db.commit(); return {"success": True, "status": new_status}

@router.delete("/{po_id}")
async def delete_purchase_order(po_id: str, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po: raise HTTPException(404, "発注書が見つかりません")
    db.delete(po); db.commit(); return {"success": True}
