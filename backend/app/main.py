from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.database import init_db
from app.api import documents, companies, products, inventory, purchase_orders, sales_orders, dashboard, forecast, notifications
from app.config import settings
from app.utils.seed import seed_demo_data

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(purchase_orders.router, prefix="/api")
app.include_router(sales_orders.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")

@app.on_event("startup")
async def startup():
    import os
    from app.config import settings
    # DBファイルを削除してスキーマを再作成（スキーマ変更時）
    db_path = str(settings.DATABASE_URL).replace("sqlite:///", "")
    if os.path.exists(db_path):
        # バージョンファイルで管理
        version_file = db_path + ".version"
        current_version = "v6_12months"
        if not os.path.exists(version_file) or open(version_file).read() != current_version:
            os.remove(db_path)
            print(f"🔄 DBをリセット（スキーマ更新: {current_version}）")
            with open(version_file, "w") as vf:
                vf.write(current_version)
    init_db()
    seed_demo_data()

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.VERSION, "app": settings.APP_NAME}



@app.get("/api/debug/pdf-text")
async def pdf_text():
    import os, glob, re
    from app.config import settings
    from app.services.forecast_service import _normalize
    try:
        from pypdf import PdfReader
    except ImportError:
        return {"error": "pypdf not available"}
    upload_dir = str(settings.UPLOAD_DIR)
    pdf_files = sorted(glob.glob(os.path.join(upload_dir, "forecast_*.pdf")), key=os.path.getmtime, reverse=True)
    if not pdf_files:
        return {"error": "PDFなし"}
    text = ""
    for page in PdfReader(pdf_files[0]).pages:
        t = page.extract_text()
        if t: text += t + "\n"
    text_norm = _normalize(text)
    patterns = re.findall(r"\d{2}-\d{2}", text_norm[:5000])
    connected = re.findall(r"(?:\d{2}-\d{2}){2,}", text_norm[:5000])
    return {
        "text_first_300": text[:300],
        "text_norm_first_300": text_norm[:300],
        "date_patterns": patterns[:20],
        "connected_patterns": connected[:10],
        "has_connected": bool(connected),
    }

@app.get("/api/debug/parse-last-pdf")
async def parse_last_pdf():
    import os, glob, re
    from app.config import settings
    from app.services.forecast_service import _normalize, _parse_forecast_text
    try:
        from pypdf import PdfReader
    except ImportError:
        return {"error": "pypdf not available"}
    upload_dir = str(settings.UPLOAD_DIR)
    pdf_files = sorted(glob.glob(os.path.join(upload_dir, "forecast_*.pdf")), key=os.path.getmtime, reverse=True)
    if not pdf_files:
        return {"error": "PDFなし", "files": os.listdir(upload_dir)}
    text = ""
    for page in PdfReader(pdf_files[0]).pages:
        t = page.extract_text()
        if t: text += t + "\n"
    text_norm = _normalize(text)
    page_boundaries = []
    for mb in re.finditer(r"((?:\d{2}-\d{2}){2,})", text_norm):
        raw = mb.group(1)
        labels_raw = re.findall(r"\d{2}-\d{2}", raw)
        labels = [f"20{m}" for m in labels_raw if 1 <= int(m.split("-")[1]) <= 12]
        if len(labels) >= 2:
            page_boundaries.append({"pos": mb.start(), "labels": labels[:6]})
    result = _parse_forecast_text(text)
    items_sample = [{"part_no": i.get("part_no"), "month_labels": i.get("month_labels"), "month_qtys": i.get("month_qtys")} for i in result.get("items", [])[:5]]
    return {"pdf": os.path.basename(pdf_files[0]), "text_len": len(text), "page_boundaries": page_boundaries, "total_items": result.get("total_items"), "items_sample": items_sample}

@app.post("/api/debug/reset-db")
async def reset_db():
    """DBを強制リセット"""
    from app.database import engine
    from app.models.base import Base
    from app.config import settings
    import os
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db_path = str(settings.DATABASE_URL).replace("sqlite:///", "")
    with open(db_path + ".version", "w") as vf:
        vf.write("v6_12months")
    from app.utils.seed import seed_demo_data
    seed_demo_data()
    return {"success": True, "message": "DBリセット完了（v6_12months）"}

@app.get("/api/debug/db-info")
async def db_info():
    """DBスキーマ情報を返す（デバッグ用）"""
    import sqlite3, os
    from app.config import settings
    db_path = str(settings.DATABASE_URL).replace("sqlite:///", "")
    version_file = db_path + ".version"
    version = open(version_file).read() if os.path.exists(version_file) else "不明"
    
    if not os.path.exists(db_path):
        return {"error": "DBファイルが存在しません", "version": version}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(forecast_items)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    
    return {
        "db_version": version,
        "forecast_items_columns": columns,
        "has_month_12": "month_12_qty" in columns,
        "has_month_7": "month_7_qty" in columns,
    }


STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse(str(STATIC_DIR / "index.html"))
