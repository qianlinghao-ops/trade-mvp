from sqlalchemy import Column, String, Enum, Text, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import uuid
import enum

class CompanyType(str, enum.Enum):
    supplier = "supplier"
    customer = "customer"

class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(200), nullable=False)
    company_type = Column(Enum(CompanyType), nullable=False)
    country = Column(String(100))
    address = Column(Text)
    contact_name = Column(String(200))
    contact_email = Column(String(200))
    contact_phone = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    sales_orders = relationship("SalesOrder", back_populates="customer")