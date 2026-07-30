from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import uuid, enum

class DocumentType(str, enum.Enum):
    po = "po"
    invoice = "invoice"
    packing_list = "packing_list"
    bl = "bl"
    coo = "coo"
    customs = "customs"
    other = "other"

class DocumentStatus(str, enum.Enum):
    uploading = "uploading"
    processing = "processing"
    review = "review"
    completed = "completed"
    error = "error"

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    doc_type = Column(Enum(DocumentType), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.uploading)
    original_filename = Column(String(300))
    stored_filename = Column(String(300))
    generated_filename = Column(String(300))
    extracted_data = Column(Text)
    confidence_score = Column(Float, default=0.0)
    purchase_order_id = Column(String, ForeignKey("purchase_orders.id"), nullable=True)
    sales_order_id = Column(String, ForeignKey("sales_orders.id"), nullable=True)
    notes = Column(Text)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    purchase_order = relationship("PurchaseOrder", back_populates="documents")
    sales_order = relationship("SalesOrder", back_populates="documents")
