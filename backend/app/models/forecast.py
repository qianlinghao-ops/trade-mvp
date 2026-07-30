"""
内示管理モデル
- ForecastOrder: 得意先からの内示（6ヶ月分）
- ForecastItem: 内示明細（月別・商品別数量）
- LeadTime: 仕入先別リードタイム
- SafetyStock: 商品別安全在庫係数
- AutoOrderProposal: 自動発注提案
- AutoOrderProposalItem: 自動発注提案明細
"""
from sqlalchemy import Column, String, Integer, Numeric, Text, DateTime, ForeignKey, Enum, Date, Float, Boolean
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import uuid
import enum

class ForecastStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    confirmed = "confirmed"
    error = "error"

class ProposalStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    ordered = "ordered"
    rejected = "rejected"

class ForecastOrder(Base):
    """得意先からの内示"""
    __tablename__ = "forecast_orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("companies.id"), nullable=False)
    forecast_month = Column(String(7), nullable=False)  # "2026-07" 形式（発行月）
    original_filename = Column(String(300))
    stored_filename = Column(String(300))
    status = Column(Enum(ForecastStatus), default=ForecastStatus.uploaded)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Company")
    items = relationship("ForecastItem", back_populates="forecast_order", cascade="all, delete-orphan")

class ForecastItem(Base):
    """内示明細（月別・商品別）"""
    __tablename__ = "forecast_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    forecast_order_id = Column(String, ForeignKey("forecast_orders.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(200), nullable=False)
    sku = Column(String(50))
    # 6ヶ月分の内示数量
    month_1_qty = Column(Integer, default=0)   # 当月
    month_2_qty = Column(Integer, default=0)   # 翌月
    month_3_qty = Column(Integer, default=0)   # 翌々月
    month_4_qty = Column(Integer, default=0)
    month_5_qty = Column(Integer, default=0)
    month_6_qty = Column(Integer, default=0)
    # 対象月
    month_1_label = Column(String(7))  # "2026-08"
    month_2_label = Column(String(7))
    month_3_label = Column(String(7))
    month_4_label = Column(String(7))
    month_5_label = Column(String(7))
    month_6_label = Column(String(7))

    forecast_order = relationship("ForecastOrder", back_populates="items")
    product = relationship("Product")

class LeadTime(Base):
    """仕入先別リードタイム（日数）"""
    __tablename__ = "lead_times"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String, ForeignKey("companies.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)  # NULL=仕入先全体のデフォルト
    lead_time_days = Column(Integer, nullable=False, default=30)
    notes = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Company")
    product = relationship("Product")

class SafetyStock(Base):
    """商品別安全在庫係数"""
    __tablename__ = "safety_stocks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False, unique=True)
    safety_stock_qty = Column(Integer, default=0)   # 安全在庫数量
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product")

class AutoOrderProposal(Base):
    """自動発注提案"""
    __tablename__ = "auto_order_proposals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String, ForeignKey("companies.id"), nullable=False)
    proposal_date = Column(Date, default=datetime.utcnow)
    target_month = Column(String(7), nullable=False)  # 対象月 "2026-08"
    status = Column(Enum(ProposalStatus), default=ProposalStatus.draft)
    total_amount = Column(Numeric(15, 2), default=0)
    currency = Column(String(10), default="JPY")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Company")
    items = relationship("AutoOrderProposalItem", back_populates="proposal", cascade="all, delete-orphan")

class AutoOrderProposalItem(Base):
    """自動発注提案明細"""
    __tablename__ = "auto_order_proposal_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    proposal_id = Column(String, ForeignKey("auto_order_proposals.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(200))
    sku = Column(String(50))
    # 計算内訳
    forecast_qty = Column(Integer, default=0)       # 内示数量
    current_stock = Column(Integer, default=0)      # 現在庫数量
    pending_order_qty = Column(Integer, default=0)  # 発注残数量
    safety_stock_qty = Column(Integer, default=0)   # 安全在庫係数
    # 発注数量 = 内示 - 現在庫 - 発注残 + 安全在庫
    proposed_qty = Column(Integer, default=0)
    unit_price = Column(Numeric(12, 2), default=0)
    amount = Column(Numeric(15, 2), default=0)
    unit = Column(String(20), default="個")
    is_adjusted = Column(Boolean, default=False)    # 手動調整済みフラグ

    proposal = relationship("AutoOrderProposal", back_populates="items")
    product = relationship("Product")