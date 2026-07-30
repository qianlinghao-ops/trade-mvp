# 🚢 貿易業務自動化システム MVP

ローカル環境で動作する貿易業務管理Webアプリケーションです。
Azure AI・Docker不要で、PythonとNode.jsがあれば動作します。

---

## 📋 機能一覧

| 機能 | 説明 |
|------|------|
| 📄 書類自動生成 | PDF/Excel/Word/画像をアップロード→OCR解析→P.O/INVOICE/Packing List自動生成 |
| 📦 発注管理 | 仕入先への発注書作成・ステータス管理・入荷時在庫自動更新 |
| 📬 受注管理 | 得意先からの受注管理・出荷時在庫自動減算 |
| 📊 在庫管理 | リアルタイム在庫管理・アラート・入出庫履歴 |
| 🏢 取引先管理 | 仕入先3社・得意先10社の管理 |
| 📋 商品マスタ | 30種類のSKU管理 |

---

## 🚀 起動方法

### 必要環境
- Python 3.10以上
- Node.js 18以上
- Tesseract OCR（日本語対応）

### Tesseractのインストール

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-jpn poppler-utils
```

**macOS:**
```bash
brew install tesseract tesseract-lang poppler
```

**Windows:**
- https://github.com/UB-Mannheim/tesseract/wiki からインストーラーをダウンロード
- 日本語言語パック（jpn）を選択してインストール

---

### バックエンド起動

```bash
cd trade-mvp/backend

# 依存関係インストール
pip install -r requirements.txt

# サーバー起動（初回起動時にデモデータが自動投入されます）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

バックエンドAPI: http://localhost:8000
APIドキュメント: http://localhost:8000/docs

---

### フロントエンド起動（開発モード）

```bash
cd trade-mvp/frontend

# 依存関係インストール
npm install

# 開発サーバー起動
npm run dev
```

フロントエンド: http://localhost:3000

---

### フロントエンドビルド（本番モード）

```bash
cd trade-mvp/frontend
npm run build

# ビルド結果をバックエンドにコピー
cp -r dist ../backend/static

# バックエンドのみで全機能が動作します
# http://localhost:8000 でアクセス
```

---

## 📁 プロジェクト構成

```
trade-mvp/
├── backend/
│   ├── app/
│   │   ├── api/           # APIエンドポイント
│   │   │   ├── documents.py      # 書類管理API
│   │   │   ├── purchase_orders.py # 発注管理API
│   │   │   ├── sales_orders.py   # 受注管理API
│   │   │   ├── inventory.py      # 在庫管理API
│   │   │   ├── companies.py      # 取引先管理API
│   │   │   ├── products.py       # 商品管理API
│   │   │   └── dashboard.py      # ダッシュボードAPI
│   │   ├── models/        # データベースモデル
│   │   ├── services/      # ビジネスロジック
│   │   │   ├── ocr_service.py         # OCR解析エンジン
│   │   │   └── document_generator.py  # PDF書類生成
│   │   ├── utils/
│   │   │   └── seed.py    # デモデータ投入
│   │   ├── config.py      # 設定
│   │   ├── database.py    # DB接続
│   │   └── main.py        # アプリエントリーポイント
│   ├── uploads/           # アップロードファイル保存先
│   ├── generated/         # 生成書類保存先
│   ├── trade.db           # SQLiteデータベース
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/           # APIクライアント
│   │   ├── components/    # 共通コンポーネント
│   │   ├── pages/         # 各画面
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Documents.tsx
│   │   │   ├── PurchaseOrders.tsx
│   │   │   ├── SalesOrders.tsx
│   │   │   ├── Inventory.tsx
│   │   │   ├── Companies.tsx
│   │   │   └── Products.tsx
│   │   ├── types/         # TypeScript型定義
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## 🔧 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | React 18 + TypeScript + Ant Design 5 + Vite |
| バックエンド | Python 3.12 + FastAPI + SQLAlchemy |
| データベース | SQLite（ローカル）→ PostgreSQL（本番）に移行可能 |
| OCR | pytesseract + pdfplumber（ローカル） |
| 書類生成 | ReportLab（PDF生成） |
| 認証 | JWT（実装済み、将来拡張用） |

---

## 📊 デモデータ

初回起動時に以下のデモデータが自動投入されます：

- **仕入先**: 3社（上海貿易、Korea Parts、Taiwan Supply）
- **得意先**: 10社（東京商事、大阪インポート等）
- **商品**: 30種類（電子部品、ディスプレイ、ケーブル等）
- **発注書**: 3件（各種ステータス）
- **受注**: 3件（各種ステータス）

---

## 🔮 今後の拡張予定（Phase 2/3）

- [ ] Azure AI Document Intelligence連携（OCR精度向上）
- [ ] B/L・原産地証明・通関書類の生成対応
- [ ] 外部取引先ポータル（社外アクセス）
- [ ] メール通知機能
- [ ] Excel形式でのレポート出力
- [ ] PostgreSQL移行（本番環境）
- [ ] Docker対応

---

## 🆘 トラブルシューティング

**OCRが動作しない場合:**
```bash
# Tesseractのインストール確認
tesseract --version
# 日本語パックの確認
tesseract --list-langs | grep jpn
```

**ポートが使用中の場合:**
```bash
# 別ポートで起動
uvicorn app.main:app --port 8001
```

**データをリセットしたい場合:**
```bash
rm trade-mvp/backend/trade.db
# 再起動するとデモデータが再投入されます
```