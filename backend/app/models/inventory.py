from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import uuid, enum

class LogType(str, enum.Enum):
    in_ = "in"
    out = "out"
    adjust = "adjust"

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False, unique=True)
    quantity = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    product = relationship("Product", back_populates="inventory")
    logs = relationship("InventoryLog", back_populates="inventory")

class InventoryLog(Base):
    __tablename__ = "inventory_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    inventory_id = Column(String, ForeignKey("inventory.id"), nullable=False)
    log_type = Column(Enum(LogType), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    reference_id = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    inventory = relationship("Inventory", back_populates="logs")
