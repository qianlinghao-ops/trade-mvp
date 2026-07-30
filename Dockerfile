FROM python:3.12-slim

# キャッシュバスター: 2026-07-30-v4
WORKDIR /app

# Pythonライブラリインストール（apt-get不使用）
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