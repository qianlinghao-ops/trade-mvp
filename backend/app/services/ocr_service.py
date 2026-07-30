"""OCRサービス - pypdf版"""
import re
from pathlib import Path
from PIL import Image
from docx import Document as DocxDocument
import openpyxl

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

def extract_text_from_pdf(file_path):
    if not PDF_AVAILABLE: return "[PDF処理不可]"
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    except Exception as e:
        print(f"pypdf error: {e}")
    return text

def extract_text_from_image(file_path):
    try:
        img = Image.open(file_path)
        w, h = img.size
        return f"[画像: {Path(file_path).name}, {w}x{h}px - 手動入力してください]"
    except Exception as e:
        return f"[画像エラー: {e}]"

def extract_text_from_docx(file_path):
    try:
        doc = DocxDocument(file_path)
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        for table in doc.tables:
            for row in table.rows:
                text += "\t".join([c.text for c in row.cells]) + "\n"
        return text
    except: return ""

def extract_text_from_excel(file_path):
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        text = ""
        for sheet in wb.worksheets:
            text += f"[Sheet: {sheet.title}]\n"
            for row in sheet.iter_rows(values_only=True):
                r = "\t".join([str(c) if c is not None else "" for c in row])
                if r.strip(): text += r + "\n"
        return text
    except: return ""

def extract_text(file_path):
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf": return extract_text_from_pdf(file_path)
    elif ext in [".jpg",".jpeg",".png",".bmp",".tiff"]: return extract_text_from_image(file_path)
    elif ext in [".docx",".doc"]: return extract_text_from_docx(file_path)
    elif ext in [".xlsx",".xls"]: return extract_text_from_excel(file_path)
    return ""

def _find(patterns, text, default=""):
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m: return m.group(1).strip()
    return default

def _find_amount(text):
    return _find([r'(?:total|合計|総額|amount)[^\d]*([0-9,]+(?:\.\d{1,2})?)', r'([0-9,]{4,}(?:\.\d{1,2})?)\s*(?:円|JPY|USD|EUR)'], text, "0")

def _find_items(text):
    items = []
    for m in re.finditer(r'([A-Za-z0-9\-\u3040-\u9fff]+)\s+(\d+)\s*(?:個|pcs|units|本|枚|箱)?\s+([0-9,]+(?:\.\d{1,2})?)', text, re.MULTILINE):
        try:
            qty = int(m.group(2)); price = float(re.sub(r'[^\d.]','',m.group(3))) if re.sub(r'[^\d.]','',m.group(3)) else 0
            items.append({"product_name": m.group(1).strip(), "quantity": qty, "unit_price": price, "amount": round(qty*price,2), "sku": "", "unit": "個"})
        except: continue
    if not items: items = [{"product_name": "（書類から自動抽出）", "quantity": 1, "unit_price": 0, "amount": 0, "sku": "", "unit": "個"}]
    return items[:10]

def parse_po(text):
    import random
    return {"doc_type": "po", "po_number": _find([r'P\.?O\.?\s*(?:No\.?|Number|番号)[:\s#]*([A-Za-z0-9\-]+)', r'発注番号[:\s]*([A-Za-z0-9\-]+)'], text, f"PO-AUTO-{random.randint(1000,9999)}"), "supplier": _find([r'(?:Supplier|仕入先|To)[:\s]+([^\n]+)'], text, "（自動抽出）"), "order_date": _find([r'(?:Date|日付|発注日)[:\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})'], text, "2026-07-30"), "currency": "JPY" if re.search(r'円|JPY', text) else ("USD" if re.search(r'USD|\$', text) else "JPY"), "total_amount": _find_amount(text), "payment_terms": _find([r'(?:Payment|支払条件)[:\s]+([^\n]+)'], text, "T/T 30 days"), "items": _find_items(text), "notes": ""}

def parse_invoice(text):
    import random
    return {"doc_type": "invoice", "invoice_number": _find([r'Invoice\s*(?:No\.?|Number|番号)[:\s#]*([A-Za-z0-9\-]+)', r'請求番号[:\s]*([A-Za-z0-9\-]+)'], text, f"INV-AUTO-{random.randint(1000,9999)}"), "customer": _find([r'(?:Bill\s*To|Sold\s*To|得意先|請求先)[:\s]+([^\n]+)'], text, "（自動抽出）"), "invoice_date": _find([r'(?:Invoice\s*Date|請求日|Date)[:\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})'], text, "2026-07-30"), "due_date": _find([r'(?:Due\s*Date|支払期限)[:\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})'], text, ""), "currency": "JPY" if re.search(r'円|JPY', text) else ("USD" if re.search(r'USD|\$', text) else "JPY"), "total_amount": _find_amount(text), "tax_amount": _find([r'(?:Tax|消費税|VAT)[:\s]*([0-9,]+(?:\.\d{1,2})?)'], text, "0"), "payment_terms": _find([r'(?:Payment|支払条件)[:\s]+([^\n]+)'], text, "T/T 30 days"), "items": _find_items(text), "notes": ""}

def parse_packing_list(text):
    import random
    return {"doc_type": "packing_list", "pl_number": _find([r'Packing\s*List\s*(?:No\.?|番号)[:\s#]*([A-Za-z0-9\-]+)'], text, f"PL-AUTO-{random.randint(1000,9999)}"), "shipper": _find([r'(?:Shipper|荷主|From)[:\s]+([^\n]+)'], text, "（自動抽出）"), "consignee": _find([r'(?:Consignee|荷受人|To)[:\s]+([^\n]+)'], text, "（自動抽出）"), "ship_date": _find([r'(?:Ship\s*Date|出荷日)[:\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})'], text, "2026-07-30"), "total_packages": _find([r'(?:Total\s*Packages?|総梱包数)[:\s]*(\d+)'], text, "1"), "total_weight": _find([r'(?:Total\s*(?:Gross\s*)?Weight|総重量)[:\s]*([0-9.]+\s*(?:kg|KG|lbs)?)'], text, ""), "items": _find_items(text), "notes": ""}

def parse_document(file_path, doc_type):
    text = extract_text(file_path) or "（テキスト抽出不可）"
    parsers = {"po": parse_po, "invoice": parse_invoice, "packing_list": parse_packing_list}
    result = parsers.get(doc_type, parse_po)(text)
    result["raw_text_preview"] = text[:500]
    filled = sum(1 for v in result.values() if v and v not in ["（自動抽出）","（書類から自動抽出）"])
    result["confidence_score"] = round(filled / len(result), 2) if result else 0.5
    return result
