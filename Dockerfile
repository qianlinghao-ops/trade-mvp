FROM python:3.12-slim

# システム依存関係を段階的にインストール（タイムアウト対策）
RUN apt-get update -o Acquire::Retries=3 && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get update -o Acquire::Retries=3 && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr-jpn \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get update -o Acquire::Retries=3 && \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    libglib2.0-0 \
    libgomp1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# Pythonライブラリインストール（段階的に）
COPY backend/requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy alembic python-multipart aiofiles pydantic pydantic-settings
RUN pip install --no-cache-dir pillow pytesseract pdf2image pdfplumber
RUN pip install --no-cache-dir python-docx openpyxl jinja2 reportlab
RUN pip install --no-cache-dir python-jose passlib httpx

# アプリコードをコピー
COPY backend/ .

# フロントエンドのビルド済みファイルをコピー
COPY frontend/dist/ ./static/

# アップロード・生成ディレクトリ作成
RUN mkdir -p uploads generated

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]