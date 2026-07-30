"""
書類生成サービス: 抽出データからPDF書類を生成する
ReportLabを使用してP.O / INVOICE / Packing Listを生成
"""
import os
import json
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from app.config import settings

# ─── フォント設定（日本語対応）───────────────────────────────────────
def _register_fonts():
    """利用可能な日本語フォントを登録"""
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJKjp-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("JaFont", fp))
                return "JaFont"
            except Exception:
                continue
    return "Helvetica"

FONT_NAME = _register_fonts()

# ─── スタイル定義 ────────────────────────────────────────────────────
def _get_styles():
    styles = getSampleStyleSheet()
    base = {"fontName": FONT_NAME, "leading": 14}
    return {
        "title": ParagraphStyle("title", fontName=FONT_NAME, fontSize=20, leading=24,
                                 alignment=TA_CENTER, textColor=colors.HexColor("#1F3864"), spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontName=FONT_NAME, fontSize=10, leading=14,
                                    alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=2),
        "label": ParagraphStyle("label", fontName=FONT_NAME, fontSize=8, leading=12,
                                 textColor=colors.HexColor("#888888")),
        "value": ParagraphStyle("value", fontName=FONT_NAME, fontSize=10, leading=14,
                                 textColor=colors.HexColor("#222222")),
        "header": ParagraphStyle("header", fontName=FONT_NAME, fontSize=9, leading=12,
                                  textColor=colors.white, alignment=TA_CENTER),
        "cell": ParagraphStyle("cell", fontName=FONT_NAME, fontSize=9, leading=12,
                                textColor=colors.HexColor("#333333")),
        "cell_right": ParagraphStyle("cell_right", fontName=FONT_NAME, fontSize=9, leading=12,
                                      textColor=colors.HexColor("#333333"), alignment=TA_RIGHT),
        "total": ParagraphStyle("total", fontName=FONT_NAME, fontSize=11, leading=14,
                                 textColor=colors.HexColor("#1F3864"), alignment=TA_RIGHT),
        "footer": ParagraphStyle("footer", fontName=FONT_NAME, fontSize=8, leading=12,
                                  textColor=colors.HexColor("#aaaaaa"), alignment=TA_CENTER),
        "normal": ParagraphStyle("normal", fontName=FONT_NAME, fontSize=9, leading=13),
    }

HEADER_COLOR = colors.HexColor("#1F3864")
ALT_ROW_COLOR = colors.HexColor("#EEF3FA")
BORDER_COLOR = colors.HexColor("#CCCCCC")

def _fmt_amount(val, currency="JPY") -> str:
    try:
        v = float(str(val).replace(",", ""))
        if currency == "JPY":
            return f"¥{v:,.0f}"
        elif currency == "USD":
            return f"${v:,.2f}"
        else:
            return f"{v:,.2f} {currency}"
    except Exception:
        return str(val)

def _info_table(data: list, styles: dict) -> Table:
    """2列の情報テーブル（ラベル：値）"""
    rows = []
    for label, value in data:
        rows.append([
            Paragraph(label, styles["label"]),
            Paragraph(str(value) if value else "—", styles["value"])
        ])
    t = Table(rows, colWidths=[40*mm, 80*mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t

def _items_table(items: list, styles: dict, currency: str = "JPY") -> Table:
    """商品明細テーブル"""
    header = [
        Paragraph("品名 / Product Name", styles["header"]),
        Paragraph("SKU", styles["header"]),
        Paragraph("数量\nQty", styles["header"]),
        Paragraph("単位\nUnit", styles["header"]),
        Paragraph("単価\nUnit Price", styles["header"]),
        Paragraph("金額\nAmount", styles["header"]),
    ]
    rows = [header]
    for i, item in enumerate(items):
        bg = ALT_ROW_COLOR if i % 2 == 0 else colors.white
        rows.append([
            Paragraph(str(item.get("product_name", "")), styles["cell"]),
            Paragraph(str(item.get("sku", "")), styles["cell"]),
            Paragraph(str(item.get("quantity", "")), styles["cell_right"]),
            Paragraph(str(item.get("unit", "個")), styles["cell"]),
            Paragraph(_fmt_amount(item.get("unit_price", 0), currency), styles["cell_right"]),
            Paragraph(_fmt_amount(item.get("amount", 0), currency), styles["cell_right"]),
        ])

    col_widths = [60*mm, 25*mm, 18*mm, 15*mm, 30*mm, 30*mm]
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        # ヘッダー
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ALT_ROW_COLOR, colors.white]),
    ])
    t.setStyle(style)
    return t

# ─── P.O 生成 ────────────────────────────────────────────────────────
def generate_po_pdf(data: dict, output_path: str) -> str:
    styles = _get_styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             leftMargin=20*mm, rightMargin=20*mm,
                             topMargin=20*mm, bottomMargin=20*mm)
    story = []
    currency = data.get("currency", "JPY")

    # タイトル
    story.append(Paragraph("PURCHASE ORDER", styles["title"]))
    story.append(Paragraph("発注書", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=HEADER_COLOR, spaceAfter=8))

    # ヘッダー情報（2列レイアウト）
    header_data = [
        [
            _info_table([
                ("P.O. Number / 発注番号", data.get("po_number", "")),
                ("Order Date / 発注日", data.get("order_date", "")),
                ("Payment Terms / 支払条件", data.get("payment_terms", "")),
            ], styles),
            _info_table([
                ("Supplier / 仕入先", data.get("supplier", "")),
                ("Currency / 通貨", currency),
                ("Notes / 備考", data.get("notes", "")),
            ], styles),
        ]
    ]
    ht = Table(header_data, colWidths=[85*mm, 85*mm])
    ht.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(ht)
    story.append(Spacer(1, 8*mm))

    # 商品明細
    story.append(Paragraph("■ 発注明細 / Order Items", styles["normal"]))
    story.append(Spacer(1, 2*mm))
    items = data.get("items", [])
    if not items:
        items = [{"product_name": "（明細なし）", "sku": "", "quantity": 0, "unit": "個", "unit_price": 0, "amount": 0}]
    story.append(_items_table(items, styles, currency))
    story.append(Spacer(1, 4*mm))

    # 合計
    total = data.get("total_amount", sum(float(str(i.get("amount", 0)).replace(",", "")) for i in items))
    total_row = Table([
        [Paragraph("合計金額 / Total Amount", styles["total"]),
         Paragraph(_fmt_amount(total, currency), styles["total"])]
    ], colWidths=[120*mm, 50*mm])
    total_row.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, HEADER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(total_row)
    story.append(Spacer(1, 12*mm))

    # 署名欄
    sign_data = [["Authorized By / 承認者", "Date / 日付", "Received By / 受領者"]]
    sign_rows = [["", "", ""]]
    st = Table(sign_data + sign_rows, colWidths=[57*mm, 57*mm, 57*mm])
    st.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#888888")),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 1), (-1, 1), 16),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(st)
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    story.append(Paragraph(f"Generated by 貿易業務自動化システム | {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["footer"]))

    doc.build(story)
    return output_path

# ─── INVOICE 生成 ────────────────────────────────────────────────────
def generate_invoice_pdf(data: dict, output_path: str) -> str:
    styles = _get_styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             leftMargin=20*mm, rightMargin=20*mm,
                             topMargin=20*mm, bottomMargin=20*mm)
    story = []
    currency = data.get("currency", "JPY")

    story.append(Paragraph("COMMERCIAL INVOICE", styles["title"]))
    story.append(Paragraph("商業請求書", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=HEADER_COLOR, spaceAfter=8))

    header_data = [[
        _info_table([
            ("Invoice No. / 請求番号", data.get("invoice_number", "")),
            ("Invoice Date / 請求日", data.get("invoice_date", "")),
            ("Due Date / 支払期限", data.get("due_date", "")),
            ("Payment Terms / 支払条件", data.get("payment_terms", "")),
        ], styles),
        _info_table([
            ("Bill To / 請求先", data.get("customer", "")),
            ("Currency / 通貨", currency),
            ("Notes / 備考", data.get("notes", "")),
        ], styles),
    ]]
    ht = Table(header_data, colWidths=[85*mm, 85*mm])
    ht.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(ht)
    story.append(Spacer(1, 8*mm))

    story.append(Paragraph("■ 請求明細 / Invoice Items", styles["normal"]))
    story.append(Spacer(1, 2*mm))
    items = data.get("items", [])
    if not items:
        items = [{"product_name": "（明細なし）", "sku": "", "quantity": 0, "unit": "個", "unit_price": 0, "amount": 0}]
    story.append(_items_table(items, styles, currency))
    story.append(Spacer(1, 4*mm))

    # 小計・税・合計
    subtotal = sum(float(str(i.get("amount", 0)).replace(",", "")) for i in items)
    tax = float(str(data.get("tax_amount", 0)).replace(",", ""))
    total = float(str(data.get("total_amount", subtotal + tax)).replace(",", ""))

    summary_rows = [
        [Paragraph("小計 / Subtotal", styles["cell_right"]), Paragraph(_fmt_amount(subtotal, currency), styles["cell_right"])],
        [Paragraph("消費税 / Tax", styles["cell_right"]), Paragraph(_fmt_amount(tax, currency), styles["cell_right"])],
        [Paragraph("合計金額 / Total Amount", styles["total"]), Paragraph(_fmt_amount(total, currency), styles["total"])],
    ]
    summary_t = Table(summary_rows, colWidths=[120*mm, 50*mm])
    summary_t.setStyle(TableStyle([
        ("LINEABOVE", (0, 2), (-1, 2), 1.5, HEADER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(summary_t)
    story.append(Spacer(1, 12*mm))

    sign_data = [["Issued By / 発行者", "Date / 日付", "Approved By / 承認者"]]
    sign_rows = [["", "", ""]]
    st = Table(sign_data + sign_rows, colWidths=[57*mm, 57*mm, 57*mm])
    st.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#888888")),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 1), (-1, 1), 16),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(st)
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    story.append(Paragraph(f"Generated by 貿易業務自動化システム | {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["footer"]))

    doc.build(story)
    return output_path

# ─── Packing List 生成 ───────────────────────────────────────────────
def generate_packing_list_pdf(data: dict, output_path: str) -> str:
    styles = _get_styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             leftMargin=20*mm, rightMargin=20*mm,
                             topMargin=20*mm, bottomMargin=20*mm)
    story = []

    story.append(Paragraph("PACKING LIST", styles["title"]))
    story.append(Paragraph("梱包明細書", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=HEADER_COLOR, spaceAfter=8))

    header_data = [[
        _info_table([
            ("P/L No. / 梱包番号", data.get("pl_number", "")),
            ("Ship Date / 出荷日", data.get("ship_date", "")),
            ("Total Packages / 総梱包数", data.get("total_packages", "")),
            ("Total Weight / 総重量", data.get("total_weight", "")),
        ], styles),
        _info_table([
            ("Shipper / 荷主", data.get("shipper", "")),
            ("Consignee / 荷受人", data.get("consignee", "")),
            ("Notes / 備考", data.get("notes", "")),
        ], styles),
    ]]
    ht = Table(header_data, colWidths=[85*mm, 85*mm])
    ht.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(ht)
    story.append(Spacer(1, 8*mm))

    story.append(Paragraph("■ 梱包明細 / Packing Details", styles["normal"]))
    story.append(Spacer(1, 2*mm))

    # Packing List専用テーブル
    pl_header = [
        Paragraph("品名 / Product Name", styles["header"]),
        Paragraph("SKU", styles["header"]),
        Paragraph("数量\nQty", styles["header"]),
        Paragraph("単位\nUnit", styles["header"]),
        Paragraph("重量(kg)\nWeight", styles["header"]),
        Paragraph("梱包数\nPkgs", styles["header"]),
    ]
    items = data.get("items", [{"product_name": "（明細なし）", "sku": "", "quantity": 0, "unit": "個"}])
    pl_rows = [pl_header]
    for i, item in enumerate(items):
        pl_rows.append([
            Paragraph(str(item.get("product_name", "")), styles["cell"]),
            Paragraph(str(item.get("sku", "")), styles["cell"]),
            Paragraph(str(item.get("quantity", "")), styles["cell_right"]),
            Paragraph(str(item.get("unit", "個")), styles["cell"]),
            Paragraph(str(item.get("weight", "")), styles["cell_right"]),
            Paragraph(str(item.get("packages", "1")), styles["cell_right"]),
        ])
    pl_t = Table(pl_rows, colWidths=[60*mm, 25*mm, 18*mm, 15*mm, 25*mm, 25*mm], repeatRows=1)
    pl_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ALT_ROW_COLOR, colors.white]),
    ]))
    story.append(pl_t)
    story.append(Spacer(1, 12*mm))

    sign_data = [["Packed By / 梱包者", "Checked By / 確認者", "Date / 日付"]]
    sign_rows = [["", "", ""]]
    st = Table(sign_data + sign_rows, colWidths=[57*mm, 57*mm, 57*mm])
    st.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#888888")),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 1), (-1, 1), 16),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(st)
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    story.append(Paragraph(f"Generated by 貿易業務自動化システム | {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["footer"]))

    doc.build(story)
    return output_path

# ─── メイン生成関数 ──────────────────────────────────────────────────
def generate_document(doc_type: str, data: dict, filename: str) -> str:
    """書類を生成してパスを返す"""
    output_path = str(settings.GENERATED_DIR / filename)
    generators = {
        "po": generate_po_pdf,
        "invoice": generate_invoice_pdf,
        "packing_list": generate_packing_list_pdf,
    }
    gen_func = generators.get(doc_type, generate_po_pdf)
    return gen_func(data, output_path)