"""
通知設定・テスト API
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.inventory import Inventory
from app.models.product import Product
from app.services.notification_service import send_low_stock_alert, send_test_email
import os

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/test")
async def test_notification(body: dict):
    """テストメール送信"""
    to = body.get("email", os.getenv("ALERT_EMAIL_TO", ""))
    if not to:
        raise HTTPException(400, "メールアドレスを指定してください")
    success = send_test_email(to)
    if success:
        return {"success": True, "message": f"テストメールを {to} に送信しました"}
    else:
        return {"success": False, "message": "メール設定が未完了です。環境変数 SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO を設定してください"}

@router.post("/send-low-stock-alert")
async def trigger_low_stock_alert(db: Session = Depends(get_db)):
    """在庫不足アラートを手動送信"""
    all_inv = db.query(Inventory).join(Product).all()
    alerts = []
    for inv in all_inv:
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
    if not alerts:
        return {"success": True, "message": "在庫不足の商品はありません", "alerts": 0}

    success = send_low_stock_alert(alerts)
    return {
        "success": success,
        "alerts_count": len(alerts),
        "message": f"{len(alerts)}件の在庫不足アラートを送信しました" if success else "メール設定が未完了です",
    }

@router.get("/settings")
async def get_notification_settings():
    """現在のメール設定状態を確認"""
    smtp_user = os.getenv("SMTP_USER", "")
    alert_to = os.getenv("ALERT_EMAIL_TO", "")
    return {
        "smtp_configured": bool(smtp_user and os.getenv("SMTP_PASSWORD")),
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": os.getenv("SMTP_PORT", "587"),
        "smtp_user": smtp_user[:3] + "***" if smtp_user else "未設定",
        "alert_email_to": alert_to if alert_to else "未設定",
        "status": "設定済み" if smtp_user else "未設定（Railwayの環境変数で設定してください）",
    }