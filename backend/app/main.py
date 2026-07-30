from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.database import init_db
from app.api import documents, companies, products, inventory, purchase_orders, sales_orders, dashboard
from app.config import settings
from app.utils.seed import seed_demo_data

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="貿易業務自動化システム API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(documents.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(purchase_orders.router, prefix="/api")
app.include_router(sales_orders.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

@app.on_event("startup")
async def startup():
    init_db()
    seed_demo_data()

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.VERSION, "app": settings.APP_NAME}

# 静的ファイル配信（フロントエンド）
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index = STATIC_DIR / "index.html"
        return FileResponse(str(index))