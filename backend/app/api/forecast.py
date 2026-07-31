"""
内示管理・自動発注提案 API
"""
import json
import re
import uuid
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, date
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.forecast import (
    ForecastOrder, ForecastItem, LeadTime, SafetyStock,
    AutoOrderProposal, AutoOrderProposalItem,
    ForecastStatus, ProposalStatus
)
from app.models.company import Company
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem, POStatus
from app.services.forecast_service import (
    extract_forecast_from_pdf, calculate_order_proposals, create_proposal_from_calculation
)
from app.services.notification_service import send_low_stock_alert, send_proposal_notification

router = APIRouter(prefix="/forecast", tags=["forecast"])

# ─── 内示管理 ─────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_forecast(
    file: UploadFile = File(...),
    customer_id: str = Form(...),
    forecast_month: str = Form(...),  # "2026-07"
    db: Session = Depends(get_db)
):
    """内示PDFをアップロードしてOCR解析"""
    ext = Path(file.filename).suffix.lower()
    stored_name = f"forecast_{uuid.uuid4()}{ext}"
    stored_path = settings.UPLOAD_DIR / stored_name

    with open(stored_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # DB登録
    forecast = ForecastOrder(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        forecast_month=forecast_month,
        original_filename=file.filename,
        stored_filename=stored_name,
        status=ForecastStatus.processing,
    )
    db.add(forecast)
    db.commit()
    db.refresh(forecast)

    # PDF解析
    try:
        extracted = extract_forecast_from_pdf(str(stored_path))
        forecast.status = ForecastStatus.confirmed

        # 内示明細を保存
        for item_data in extracted.get("items", []):
            # 部番（SKU）から商品マスタを検索
            product = None
            part_no = item_data.get("part_no") or item_data.get("sku", "")
            if part_no:
                # 完全一致
                product = db.query(Product).filter(Product.sku == part_no).first()
                # スペース除去して部分一致
                if not product:
                    clean_part = re.sub(r"\s+", "", part_no)
                    for p in db.query(Product).all():
                        if re.sub(r"\s+", "", p.sku) == clean_part:
                            product = p
                            break

            # 12ヶ月分のデータを準備
            month_qtys_12 = item_data.get("month_qtys", [])
            month_labels_12 = item_data.get("month_labels", [])
            while len(month_qtys_12) < 12:
                month_qtys_12.append(0)
            while len(month_labels_12) < 12:
                month_labels_12.append("")

            fi = ForecastItem(
                id=str(uuid.uuid4()),
                forecast_order_id=forecast.id,
                product_id=product.id if product else None,
                product_name=item_data.get("product_name", ""),
                sku=part_no,
                month_1_qty=month_qtys_12[0], month_1_label=month_labels_12[0],
                month_2_qty=month_qtys_12[1], month_2_label=month_labels_12[1],
                month_3_qty=month_qtys_12[2], month_3_label=month_labels_12[2],
                month_4_qty=month_qtys_12[3], month_4_label=month_labels_12[3],
                month_5_qty=month_qtys_12[4], month_5_label=month_labels_12[4],
                month_6_qty=month_qtys_12[5], month_6_label=month_labels_12[5],
                month_7_qty=month_qtys_12[6], month_7_label=month_labels_12[6],
                month_8_qty=month_qtys_12[7], month_8_label=month_labels_12[7],
                month_9_qty=month_qtys_12[8], month_9_label=month_labels_12[8],
                month_10_qty=month_qtys_12[9], month_10_label=month_labels_12[9],
                month_11_qty=month_qtys_12[10], month_11_label=month_labels_12[10],
                month_12_qty=month_qtys_12[11], month_12_label=month_labels_12[11],
            )
            db.add(fi)

        db.commit()
    except Exception as e:
        forecast.status = ForecastStatus.error
        db.commit()
        raise HTTPException(500, f"PDF解析エラー: {str(e)}")

    db.refresh(forecast)
    return {
        "forecast_id": forecast.id,
        "status": forecast.status,
        "extracted": extracted,
        "items_count": len(extracted.get("items", [])),
    }

@router.get("")
async def list_forecasts(db: Session = Depends(get_db)):
    """内示一覧"""
    forecasts = db.query(ForecastOrder).order_by(ForecastOrder.created_at.desc()).all()
    return {
        "total": len(forecasts),
        "items": [
            {
                "id": f.id,
                "customer_name": f.customer.company_name if f.customer else "",
                "forecast_month": f.forecast_month,
                "original_filename": f.original_filename,
                "status": f.status,
                "items_count": len(f.items),
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in forecasts
        ]
    }


@router.delete("/{forecast_id}")
async def delete_forecast(forecast_id: str, db: Session = Depends(get_db)):
    """内示を削除"""
    f = db.query(ForecastOrder).filter(ForecastOrder.id == forecast_id).first()
    if not f:
        raise HTTPException(404, "内示が見つかりません")
    db.delete(f)
    db.commit()
    return {"success": True}

@router.get("/{forecast_id}")
async def get_forecast(forecast_id: str, db: Session = Depends(get_db)):
    """内示詳細"""
    f = db.query(ForecastOrder).filter(ForecastOrder.id == forecast_id).first()
    if not f:
        raise HTTPException(404, "内示が見つかりません")
    return {
        "id": f.id,
        "customer_name": f.customer.company_name if f.customer else "",
        "forecast_month": f.forecast_month,
        "status": f.status,
        "items": [
            {
                "id": fi.id,
                "product_id": fi.product_id,
                "product_name": fi.product_name,
                "sku": fi.sku,
                "months": [
                    {"label": fi.month_1_label, "qty": fi.month_1_qty},
                    {"label": fi.month_2_label, "qty": fi.month_2_qty},
                    {"label": fi.month_3_label, "qty": fi.month_3_qty},
                    {"label": fi.month_4_label, "qty": fi.month_4_qty},
                    {"label": fi.month_5_label, "qty": fi.month_5_qty},
                    {"label": fi.month_6_label, "qty": fi.month_6_qty},
                    {"label": fi.month_7_label, "qty": fi.month_7_qty},
                    {"label": fi.month_8_label, "qty": fi.month_8_qty},
                    {"label": fi.month_9_label, "qty": fi.month_9_qty},
                    {"label": fi.month_10_label, "qty": fi.month_10_qty},
                    {"label": fi.month_11_label, "qty": fi.month_11_qty},
                    {"label": fi.month_12_label, "qty": fi.month_12_qty},
                ]
            }
            for fi in f.items
        ]
    }

@router.put("/{forecast_id}/items/{item_id}")
async def update_forecast_item(
    forecast_id: str, item_id: str, body: dict, db: Session = Depends(get_db)
):
    """内示明細を手動修正"""
    fi = db.query(ForecastItem).filter(ForecastItem.id == item_id).first()
    if not fi:
        raise HTTPException(404, "内示明細が見つかりません")
    for k, v in body.items():
        if hasattr(fi, k):
            setattr(fi, k, v)
    db.commit()
    return {"success": True}

# ─── リードタイム管理 ─────────────────────────────────────────────────

@router.get("/lead-times/list")
async def list_lead_times(db: Session = Depends(get_db)):
    lts = db.query(LeadTime).all()
    return {
        "items": [
            {
                "id": lt.id,
                "supplier_id": lt.supplier_id,
                "supplier_name": lt.supplier.company_name if lt.supplier else "",
                "product_id": lt.product_id,
                "product_name": lt.product.product_name if lt.product else "（全商品デフォルト）",
                "lead_time_days": lt.lead_time_days,
                "notes": lt.notes,
            }
            for lt in lts
        ]
    }

@router.post("/lead-times")
async def create_lead_time(body: dict, db: Session = Depends(get_db)):
    lt = LeadTime(
        id=str(uuid.uuid4()),
        supplier_id=body.get("supplier_id"),
        product_id=body.get("product_id"),
        lead_time_days=body.get("lead_time_days", 30),
        notes=body.get("notes", ""),
    )
    db.add(lt)
    db.commit()
    return {"id": lt.id, "success": True}

@router.put("/lead-times/{lt_id}")
async def update_lead_time(lt_id: str, body: dict, db: Session = Depends(get_db)):
    lt = db.query(LeadTime).filter(LeadTime.id == lt_id).first()
    if not lt:
        raise HTTPException(404, "リードタイムが見つかりません")
    for k, v in body.items():
        if hasattr(lt, k):
            setattr(lt, k, v)
    db.commit()
    return {"success": True}

# ─── 安全在庫管理 ─────────────────────────────────────────────────────

@router.get("/safety-stocks/list")
async def list_safety_stocks(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    result = []
    for p in products:
        ss = db.query(SafetyStock).filter(SafetyStock.product_id == p.id).first()
        result.append({
            "product_id": p.id,
            "sku": p.sku,
            "product_name": p.product_name,
            "safety_stock_qty": ss.safety_stock_qty if ss else 0,
            "safety_stock_id": ss.id if ss else None,
        })
    return {"items": result}

@router.put("/safety-stocks/{product_id}")
async def update_safety_stock(product_id: str, body: dict, db: Session = Depends(get_db)):
    ss = db.query(SafetyStock).filter(SafetyStock.product_id == product_id).first()
    if ss:
        ss.safety_stock_qty = body.get("safety_stock_qty", 0)
    else:
        ss = SafetyStock(
            id=str(uuid.uuid4()),
            product_id=product_id,
            safety_stock_qty=body.get("safety_stock_qty", 0),
        )
        db.add(ss)
    db.commit()
    return {"success": True}

# ─── 自動発注提案 ─────────────────────────────────────────────────────

@router.post("/proposals/calculate")
async def calculate_proposals(body: dict, db: Session = Depends(get_db)):
    """発注数量を自動計算"""
    supplier_id = body.get("supplier_id")
    target_month = body.get("target_month")
    if not supplier_id or not target_month:
        raise HTTPException(400, "supplier_idとtarget_monthは必須です")

    proposals = calculate_order_proposals(db, supplier_id, target_month)
    return {
        "supplier_id": supplier_id,
        "target_month": target_month,
        "items": proposals,
        "total_amount": sum(p.get("amount", 0) for p in proposals),
        "formula_note": "発注数量 = 内示数量 - 現在庫数量 - 発注残数量 + 安全在庫係数",
    }

@router.post("/proposals")
async def create_proposal(body: dict, db: Session = Depends(get_db)):
    """発注提案を保存"""
    supplier_id = body.get("supplier_id")
    target_month = body.get("target_month")
    items = body.get("items", [])
    
    # supplier_idが空の場合、最初の仕入先を使用
    if not supplier_id:
        from app.models.company import Company, CompanyType
        first_supplier = db.query(Company).filter(Company.company_type == CompanyType.supplier).first()
        if first_supplier:
            supplier_id = first_supplier.id
        else:
            supplier_id = "unknown"
    
    proposal = create_proposal_from_calculation(db, supplier_id, target_month, items)
    return {"proposal_id": proposal.id, "status": proposal.status, "total_amount": float(proposal.total_amount)}

@router.get("/proposals/list")
async def list_proposals(db: Session = Depends(get_db)):
    proposals = db.query(AutoOrderProposal).order_by(AutoOrderProposal.created_at.desc()).all()
    return {
        "total": len(proposals),
        "items": [
            {
                "id": p.id,
                "supplier_name": p.supplier.company_name if p.supplier else "",
                "target_month": p.target_month,
                "status": p.status,
                "total_amount": float(p.total_amount) if p.total_amount else 0,
                "items_count": len(p.items),
                "proposal_date": p.proposal_date.isoformat() if p.proposal_date else None,
            }
            for p in proposals
        ]
    }

@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str, db: Session = Depends(get_db)):
    p = db.query(AutoOrderProposal).filter(AutoOrderProposal.id == proposal_id).first()
    if not p:
        raise HTTPException(404, "発注提案が見つかりません")
    return {
        "id": p.id,
        "supplier_name": p.supplier.company_name if p.supplier else "",
        "target_month": p.target_month,
        "status": p.status,
        "total_amount": float(p.total_amount) if p.total_amount else 0,
        "proposal_date": p.proposal_date.isoformat() if p.proposal_date else None,
        "items": [
            {
                "id": pi.id,
                "product_name": pi.product_name,
                "sku": pi.sku,
                "forecast_qty": pi.forecast_qty,
                "current_stock": pi.current_stock,
                "pending_order_qty": pi.pending_order_qty,
                "safety_stock_qty": pi.safety_stock_qty,
                "proposed_qty": pi.proposed_qty,
                "unit_price": float(pi.unit_price) if pi.unit_price else 0,
                "amount": float(pi.amount) if pi.amount else 0,
                "unit": pi.unit,
                "formula": f"{pi.forecast_qty} - {pi.current_stock} - {pi.pending_order_qty} + {pi.safety_stock_qty} = {pi.proposed_qty}",
            }
            for pi in p.items
        ]
    }

@router.put("/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str, db: Session = Depends(get_db)):
    """発注提案を承認して発注書を自動作成"""
    p = db.query(AutoOrderProposal).filter(AutoOrderProposal.id == proposal_id).first()
    if not p:
        raise HTTPException(404, "発注提案が見つかりません")

    # 発注書を自動作成
    from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
    count = db.query(PurchaseOrder).count()
    po = PurchaseOrder(
        id=str(uuid.uuid4()),
        po_number=f"PO-{datetime.now().strftime('%Y%m')}-{count+1:04d}",
        supplier_id=p.supplier_id,
        status=POStatus.draft,
        order_date=date.today(),
        currency=p.currency,
        payment_terms="T/T 30 days",
        notes=f"自動発注提案 {p.target_month} より生成",
        total_amount=p.total_amount,
    )
    db.add(po)
    db.flush()

    for pi in p.items:
        if pi.proposed_qty > 0:
            item = PurchaseOrderItem(
                id=str(uuid.uuid4()),
                purchase_order_id=po.id,
                product_id=pi.product_id,
                product_name=pi.product_name,
                sku=pi.sku,
                quantity=pi.proposed_qty,
                unit_price=pi.unit_price,
                amount=pi.amount,
                unit=pi.unit,
            )
            db.add(item)

    p.status = ProposalStatus.approved
    db.commit()

    # 通知送信
    try:
        send_proposal_notification(p, po)
    except Exception:
        pass

    return {
        "success": True,
        "purchase_order_id": po.id,
        "po_number": po.po_number,
        "message": f"発注書 {po.po_number} を自動作成しました",
    }

@router.put("/proposals/{proposal_id}/items/{item_id}")
async def update_proposal_item(proposal_id: str, item_id: str, body: dict, db: Session = Depends(get_db)):
    """発注提案明細を手動調整"""
    pi = db.query(AutoOrderProposalItem).filter(AutoOrderProposalItem.id == item_id).first()
    if not pi:
        raise HTTPException(404, "明細が見つかりません")
    if "proposed_qty" in body:
        pi.proposed_qty = body["proposed_qty"]
        pi.amount = pi.proposed_qty * float(pi.unit_price)
        pi.is_adjusted = True
    db.commit()
    return {"success": True}