from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.purchase_order import PurchaseOrder, POStatus
from app.models.sales_order import SalesOrder, SOStatus
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.document import Document

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("")
async def get_dashboard(db: Session = Depends(get_db)):
    po_total = db.query(PurchaseOrder).count()
    po_active = db.query(PurchaseOrder).filter(PurchaseOrder.status.in_([POStatus.ordered, POStatus.confirmed, POStatus.in_transit])).count()
    po_pending = db.query(PurchaseOrder).filter(PurchaseOrder.status == POStatus.draft).count()
    so_total = db.query(SalesOrder).count()
    so_active = db.query(SalesOrder).filter(SalesOrder.status.in_([SOStatus.received, SOStatus.confirmed, SOStatus.preparing])).count()
    so_shipped = db.query(SalesOrder).filter(SalesOrder.status == SOStatus.shipped).count()
    all_inv = db.query(Inventory).join(Product).all()
    low_stock_count = sum(1 for inv in all_inv if inv.quantity <= (inv.product.min_stock_qty if inv.product else 0))
    doc_total = db.query(Document).count()
    doc_recent = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
    recent_po = db.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).limit(5).all()
    recent_so = db.query(SalesOrder).order_by(SalesOrder.created_at.desc()).limit(5).all()
    return {
        "purchase_orders": {"total": po_total, "active": po_active, "pending": po_pending},
        "sales_orders": {"total": so_total, "active": so_active, "shipped": so_shipped},
        "inventory": {"total_skus": db.query(Product).count(), "low_stock_alerts": low_stock_count},
        "documents": {"total": doc_total, "recent": [{"id": d.id, "doc_type": d.doc_type, "original_filename": d.original_filename, "status": d.status, "created_at": d.created_at.isoformat() if d.created_at else None} for d in doc_recent]},
        "recent_purchase_orders": [{"id": po.id, "po_number": po.po_number, "supplier_name": po.supplier.company_name if po.supplier else "", "status": po.status, "total_amount": float(po.total_amount) if po.total_amount else 0, "currency": po.currency, "order_date": po.order_date.isoformat() if po.order_date else None} for po in recent_po],
        "recent_sales_orders": [{"id": so.id, "so_number": so.so_number, "customer_name": so.customer.company_name if so.customer else "", "status": so.status, "total_amount": float(so.total_amount) if so.total_amount else 0, "currency": so.currency, "order_date": so.order_date.isoformat() if so.order_date else None} for so in recent_so],
    }
