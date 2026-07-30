from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product import Product
from app.models.inventory import Inventory
import uuid

router = APIRouter(prefix="/products", tags=["products"])

@router.get("")
async def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.sku).all()
    result = []
    for p in products:
        inv = db.query(Inventory).filter(Inventory.product_id == p.id).first()
        result.append({"id": p.id, "sku": p.sku, "product_name": p.product_name, "product_name_en": p.product_name_en, "hs_code": p.hs_code, "unit_price": float(p.unit_price) if p.unit_price else 0, "currency": p.currency, "unit": p.unit, "min_stock_qty": p.min_stock_qty, "current_stock": inv.quantity if inv else 0, "is_low_stock": (inv.quantity if inv else 0) <= p.min_stock_qty, "supplier_id": p.supplier_id})
    return {"total": len(result), "items": result}

@router.post("")
async def create_product(body: dict, db: Session = Depends(get_db)):
    product = Product(id=str(uuid.uuid4()), sku=body.get("sku", f"SKU-{uuid.uuid4().hex[:6].upper()}"), product_name=body.get("product_name",""), product_name_en=body.get("product_name_en",""), hs_code=body.get("hs_code",""), unit_price=body.get("unit_price",0), currency=body.get("currency","JPY"), unit=body.get("unit","個"), min_stock_qty=body.get("min_stock_qty",0), supplier_id=body.get("supplier_id"), description=body.get("description",""))
    db.add(product); db.flush()
    inv = Inventory(id=str(uuid.uuid4()), product_id=product.id, quantity=body.get("initial_stock",0))
    db.add(inv); db.commit(); db.refresh(product)
    return {"id": product.id, "sku": product.sku, "product_name": product.product_name}

@router.get("/{product_id}")
async def get_product(product_id: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p: raise HTTPException(404, "商品が見つかりません")
    inv = db.query(Inventory).filter(Inventory.product_id == p.id).first()
    return {"id": p.id, "sku": p.sku, "product_name": p.product_name, "unit_price": float(p.unit_price) if p.unit_price else 0, "currency": p.currency, "unit": p.unit, "min_stock_qty": p.min_stock_qty, "current_stock": inv.quantity if inv else 0, "supplier_id": p.supplier_id}

@router.put("/{product_id}")
async def update_product(product_id: str, body: dict, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p: raise HTTPException(404, "商品が見つかりません")
    for k, v in body.items():
        if hasattr(p, k) and k not in ["id","created_at"]: setattr(p, k, v)
    db.commit(); return {"success": True}

@router.delete("/{product_id}")
async def delete_product(product_id: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p: raise HTTPException(404, "商品が見つかりません")
    db.delete(p); db.commit(); return {"success": True}
