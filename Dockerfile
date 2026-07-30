FROM python:3.12-slim

# キャッシュバスター: 2026-07-30-v5
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY frontend/dist/ ./static/

RUN mkdir -p uploads generated

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
