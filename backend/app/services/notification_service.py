"""
通知サービス
- 在庫不足アラートメール
- 発注提案通知メール
- SMTPまたはSendGrid対応
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional

# ─── メール設定（環境変数から取得）────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")
SYSTEM_NAME = "貿易業務自動化システム"

def _send_email(to: str, subject: str, body_html: str) -> bool:
    """メール送信（SMTP）"""
    if not SMTP_USER or not SMTP_PASSWORD or not to:
        print(f"⚠️ メール設定なし - 送信スキップ: {subject}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SYSTEM_NAME} <{SMTP_USER}>"
        msg["To"] = to
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to, msg.as_string())
        print(f"✅ メール送信成功: {subject} → {to}")
        return True
    except Exception as e:
        print(f"❌ メール送信エラー: {e}")
        return False

def send_low_stock_alert(alerts: List[dict]) -> bool:
    """在庫不足アラートメール"""
    if not alerts:
        return False

    rows = ""
    for a in alerts:
        shortage = a.get("min_stock_qty", 0) - a.get("current_qty", 0)
        rows += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ddd;">{a.get('sku','')}</td>
            <td style="padding:8px;border:1px solid #ddd;">{a.get('product_name','')}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right;color:#ff4d4f;">
                <strong>{a.get('current_qty',0)}</strong>
            </td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right;">{a.get('min_stock_qty',0)}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right;color:#ff4d4f;">
                <strong>-{shortage}</strong>
            </td>
        </tr>"""

    body = f"""
    <html><body style="font-family:sans-serif;color:#333;">
    <div style="max-width:700px;margin:0 auto;padding:20px;">
        <div style="background:#1F3864;color:white;padding:20px;border-radius:8px 8px 0 0;">
            <h2 style="margin:0;">⚠️ 在庫不足アラート</h2>
            <p style="margin:4px 0 0;">{SYSTEM_NAME}</p>
        </div>
        <div style="background:#fff;border:1px solid #ddd;padding:20px;">
            <p>以下の商品が最低在庫数を下回っています。発注をご検討ください。</p>
            <p style="color:#888;font-size:12px;">通知日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
            <table style="width:100%;border-collapse:collapse;margin-top:16px;">
                <thead>
                    <tr style="background:#f5f5f5;">
                        <th style="padding:8px;border:1px solid #ddd;text-align:left;">SKU</th>
                        <th style="padding:8px;border:1px solid #ddd;text-align:left;">商品名</th>
                        <th style="padding:8px;border:1px solid #ddd;text-align:right;">現在庫</th>
                        <th style="padding:8px;border:1px solid #ddd;text-align:right;">最低在庫</th>
                        <th style="padding:8px;border:1px solid #ddd;text-align:right;">不足数</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <div style="margin-top:20px;padding:12px;background:#fff2f0;border-radius:4px;border-left:4px solid #ff4d4f;">
                <strong>対応が必要な商品: {len(alerts)}件</strong>
            </div>
        </div>
        <div style="background:#f5f5f5;padding:12px;text-align:center;font-size:12px;color:#888;border-radius:0 0 8px 8px;">
            {SYSTEM_NAME} | 自動送信メール
        </div>
    </div>
    </body></html>
    """
    return _send_email(
        to=ALERT_EMAIL_TO,
        subject=f"【在庫アラート】{len(alerts)}件の商品が最低在庫数を下回っています",
        body_html=body,
    )

def send_proposal_notification(proposal, purchase_order) -> bool:
    """発注提案承認・発注書作成通知メール"""
    rows = ""
    for pi in proposal.items:
        if pi.proposed_qty > 0:
            rows += f"""
            <tr>
                <td style="padding:8px;border:1px solid #ddd;">{pi.sku}</td>
                <td style="padding:8px;border:1px solid #ddd;">{pi.product_name}</td>
                <td style="padding:8px;border:1px solid #ddd;text-align:right;">{pi.forecast_qty}</td>
                <td style="padding:8px;border:1px solid #ddd;text-align:right;">{pi.current_stock}</td>
                <td style="padding:8px;border:1px solid #ddd;text-align:right;">{pi.pending_order_qty}</td>
                <td style="padding:8px;border:1px solid #ddd;text-align:right;">{pi.safety_stock_qty}</td>
                <td style="padding:8px;border:1px solid #ddd;text-align:right;color:#1F3864;">
                    <strong>{pi.proposed_qty}</strong>
                </td>
            </tr>"""

    supplier_name = proposal.supplier.company_name if proposal.supplier else ""
    body = f"""
    <html><body style="font-family:sans-serif;color:#333;">
    <div style="max-width:800px;margin:0 auto;padding:20px;">
        <div style="background:#1F3864;color:white;padding:20px;border-radius:8px 8px 0 0;">
            <h2 style="margin:0;">📦 自動発注提案 承認・発注書作成完了</h2>
            <p style="margin:4px 0 0;">{SYSTEM_NAME}</p>
        </div>
        <div style="background:#fff;border:1px solid #ddd;padding:20px;">
            <table style="width:100%;margin-bottom:16px;">
                <tr><td style="color:#888;width:140px;">発注書番号</td><td><strong>{purchase_order.po_number}</strong></td></tr>
                <tr><td style="color:#888;">仕入先</td><td>{supplier_name}</td></tr>
                <tr><td style="color:#888;">対象月</td><td>{proposal.target_month}</td></tr>
                <tr><td style="color:#888;">合計金額</td><td><strong>¥{float(proposal.total_amount):,.0f}</strong></td></tr>
                <tr><td style="color:#888;">作成日時</td><td>{datetime.now().strftime('%Y年%m月%d日 %H:%M')}</td></tr>
            </table>
            <h3 style="color:#1F3864;">発注明細（計算内訳）</h3>
            <p style="font-size:12px;color:#888;">計算式: 発注数量 = 内示数量 - 現在庫 - 発注残 + 安全在庫</p>
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="background:#1F3864;color:white;">
                        <th style="padding:8px;text-align:left;">SKU</th>
                        <th style="padding:8px;text-align:left;">商品名</th>
                        <th style="padding:8px;text-align:right;">内示数量</th>
                        <th style="padding:8px;text-align:right;">現在庫</th>
                        <th style="padding:8px;text-align:right;">発注残</th>
                        <th style="padding:8px;text-align:right;">安全在庫</th>
                        <th style="padding:8px;text-align:right;">発注数量</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <div style="margin-top:20px;padding:12px;background:#e8f0fe;border-radius:4px;border-left:4px solid #1F3864;">
                <strong>✅ 発注書 {purchase_order.po_number} が自動作成されました。</strong><br>
                <span style="font-size:12px;color:#555;">システムにログインして内容を確認・送付してください。</span>
            </div>
        </div>
        <div style="background:#f5f5f5;padding:12px;text-align:center;font-size:12px;color:#888;border-radius:0 0 8px 8px;">
            {SYSTEM_NAME} | 自動送信メール
        </div>
    </div>
    </body></html>
    """
    return _send_email(
        to=ALERT_EMAIL_TO,
        subject=f"【発注書作成】{purchase_order.po_number} - {supplier_name} ({proposal.target_month})",
        body_html=body,
    )

def send_test_email(to: str) -> bool:
    """テストメール送信"""
    body = f"""
    <html><body style="font-family:sans-serif;">
    <div style="max-width:500px;margin:0 auto;padding:20px;">
        <div style="background:#1F3864;color:white;padding:20px;border-radius:8px;">
            <h2>✅ メール設定テスト成功</h2>
            <p>{SYSTEM_NAME} からのテストメールです。</p>
            <p>送信日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
        </div>
    </div>
    </body></html>
    """
    return _send_email(to=to, subject=f"【テスト】{SYSTEM_NAME} メール設定確認", body_html=body)