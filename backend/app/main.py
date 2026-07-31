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
