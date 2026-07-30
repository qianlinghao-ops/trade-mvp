from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.sales_order import SalesOrder, SalesOrderItem, SOStatus
from app.models.inventory import Inventory, InventoryLog
import uuid
from datetime import datetime, date

router = APIRouter(prefix="/sales-orders", tags=["sales_orders"])

def _so_to_dict(so: SalesOrder) -> dict:
    return {
        "id": so.id,
        "so_number": so.so_number,
        "customer_id": so.customer_id,
        "customer_name": so.customer.company_name if so.customer else "",
        "status": so.status,
        "order_date": so.order_date.isoformat() if so.order_date else None,
        "delivery_date": so.delivery_date.isoformat() if so.delivery_date else None,
        "total_amount": float(so.total_amount) if so.total_amount else 0,
        "currency": so.currency,
        "payment_terms": so.payment_terms,
        "destination": so.destination,
        "notes": so.notes,
        "created_at": so.created_at.isoformat() if so.created_at else None,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "sku": item.sku,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price) if item.unit_price else 0,
                "amount": float(item.amount) if item.amount else 0,
                "unit": item.unit,
            }
            for item in so.items
        ],
    }

@router.get("")
async def list_sales_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(SalesOrder)
    if status:
        q = q.filter(SalesOrder.status == status)
    orders = q.order_by(SalesOrder.created_at.desc()).all()
    return {"total": len(orders), "items": [_so_to_dict(o) for o in orders]}

@router.post("")
async def create_sales_order(body: dict, db: Session = Depends(get_db)):
    count = db.query(SalesOrder).count()
    so_number = body.get("so_number") or f"SO-{datetime.now().strftime('%Y%m')}-{count+1:04d}"

    so = SalesOrder(
        id=str(uuid.uuid4()),
        so_number=so_number,
        customer_id=body.get("customer_id", ""),
        status=body.get("status", SOStatus.draft),
        order_date=date.fromisoformat(body["order_date"]) if body.get("order_date") else date.today(),
        delivery_date=date.fromisoformat(body["delivery_date"]) if body.get("delivery_date") else None,
        currency=body.get("currency", "JPY"),
        payment_terms=body.get("payment_terms", ""),
        shipping_terms=body.get("shipping_terms", ""),
        destination=body.get("destination", ""),
        notes=body.get("notes", ""),
    )
    db.add(so)
    db.flush()

    total = 0
    for item_data in body.get("items", []):
        qty = int(item_data.get("quantity", 1))
        price = float(item_data.get("unit_price", 0))
        amount = qty * price
        total += amount
        item = SalesOrderItem(
            id=str(uuid.uuid4()),
            sales_order_id=so.id,
            product_id=item_data.get("product_id"),
            product_name=item_data.get("product_name", ""),
            sku=item_data.get("sku", ""),
            quantity=qty,
            unit_price=price,
            amount=amount,
            unit=item_data.get("unit", "個"),
        )
        db.add(item)

    so.total_amount = total
    db.commit()
    db.refresh(so)
    return _so_to_dict(so)

@router.get("/{so_id}")
async def get_sales_order(so_id: str, db: Session = Depends(get_db)):
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise HTTPException(404, "受注が見つかりません")
    return _so_to_dict(so)

@router.put("/{so_id}/status")
async def update_so_status(so_id: str, body: dict, db: Session = Depends(get_db)):
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise HTTPException(404, "受注が見つかりません")

    new_status = body.get("status")
    so.status = new_status
    so.updated_at = datetime.utcnow()

    # 出荷済みになったら在庫を自動減算
    if new_status == SOStatus.shipped:
        for item in so.items:
            if item.product_id:
                inv = db.query(Inventory).filter(Inventory.product_id == item.product_id).first()
                if inv:
                    inv.quantity = max(0, inv.quantity - item.quantity)
                    inv.updated_at = datetime.utcnow()
                    log = InventoryLog(
                        id=str(uuid.uuid4()),
                        inventory_id=inv.id,
                        log_type="out",
                        quantity_change=-item.quantity,
                        quantity_after=inv.quantity,
                        reference_id=so.so_number,
                        notes=f"受注 {so.so_number} 出荷",
                    )
                    db.add(log)

    db.commit()
    return {"success": True, "status": new_status}

@router.put("/{so_id}")
async def update_sales_order(so_id: str, body: dict, db: Session = Depends(get_db)):
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise HTTPException(404, "受注が見つかりません")
    for k, v in body.items():
        if hasattr(so, k) and k not in ["id", "created_at", "items"]:
            setattr(so, k, v)
    db.commit()
    return {"success": True}

@router.delete("/{so_id}")
async def delete_sales_order(so_id: str, db: Session = Depends(get_db)):
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise HTTPException(404, "受注が見つかりません")
    db.delete(so)
    db.commit()
    return {"success": True}