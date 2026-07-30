FROM python:3.12-slim

# 最小限の依存関係のみ（Tesseract不使用・Railway対応）
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libglib2.0-0 \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# Pythonライブラリインストール
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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