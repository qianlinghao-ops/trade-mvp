from sqlalchemy import Column, String, Numeric, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import uuid

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sku = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(200), nullable=False)
    product_name_en = Column(String(200))
    hs_code = Column(String(20))
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="JPY")
    unit = Column(String(20), default="個")
    min_stock_qty = Column(Integer, default=0)
    supplier_id = Column(String, ForeignKey("companies.id"), nullable=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inventory = relationship("Inventory", back_populates="product", uselist=False)
    purchase_order_items = relationship("PurchaseOrderItem", back_populates="product")
    sales_order_items = relationship("SalesOrderItem", back_populates="product")