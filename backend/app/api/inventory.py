from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.inventory import Inventory, InventoryLog, LogType
from app.models.product import Product
import uuid
from datetime import datetime

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("")
async def list_inventory(db: Session = Depends(get_db)):
    items = db.query(Inventory).join(Product).all()
    result = []
    for inv in items:
        p = inv.product
        result.append({
            "id": inv.id,
            "product_id": inv.product_id,
            "sku": p.sku if p else "",
            "product_name": p.product_name if p else "",
            "quantity": inv.quantity,
            "min_stock_qty": p.min_stock_qty if p else 0,
            "is_low_stock": inv.quantity <= (p.min_stock_qty if p else 0),
            "unit": p.unit if p else "個",
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
        })
    return {"total": len(result), "items": result}

@router.get("/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    """在庫アラート（最低在庫数以下の商品）"""
    items = db.query(Inventory).join(Product).all()
    alerts = []
    for inv in items:
        p = inv.product
        if p and inv.quantity <= p.min_stock_qty:
            alerts.append({
                "product_id": inv.product_id,
                "sku": p.sku,
                "product_name": p.product_name,
                "current_qty": inv.quantity,
                "min_stock_qty": p.min_stock_qty,
                "shortage": p.min_stock_qty - inv.quantity,
            })
    return {"total": len(alerts), "items": alerts}

@router.post("/{product_id}/adjust")
async def adjust_inventory(
    product_id: str,
    body: dict,
    db: Session = Depends(get_db)
):
    """在庫数を調整（入荷・出荷・棚卸）"""
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(404, "在庫レコードが見つかりません")

    log_type = body.get("log_type", "adjust")
    quantity_change = int(body.get("quantity_change", 0))
    notes = body.get("notes", "")

    if log_type == "out" and inv.quantity + quantity_change < 0:
        raise HTTPException(400, "在庫数が不足しています")

    inv.quantity += quantity_change
    inv.updated_at = datetime.utcnow()

    log = InventoryLog(
        id=str(uuid.uuid4()),
        inventory_id=inv.id,
        log_type=log_type,
        quantity_change=quantity_change,
        quantity_after=inv.quantity,
        reference_id=body.get("reference_id", ""),
        notes=notes,
    )
    db.add(log)
    db.commit()
    return {
        "success": True,
        "product_id": product_id,
        "new_quantity": inv.quantity,
        "change": quantity_change,
    }

@router.get("/{product_id}/logs")
async def get_inventory_logs(product_id: str, db: Session = Depends(get_db)):
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(404, "在庫レコードが見つかりません")
    logs = db.query(InventoryLog).filter(
        InventoryLog.inventory_id == inv.id
    ).order_by(InventoryLog.created_at.desc()).limit(50).all()
    return {
        "items": [
            {
                "id": l.id,
                "log_type": l.log_type,
                "quantity_change": l.quantity_change,
                "quantity_after": l.quantity_after,
                "notes": l.notes,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]
    }