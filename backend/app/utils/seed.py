"""
デモデータ投入スクリプト
初回起動時にサンプルデータを自動生成する
"""
from app.database import SessionLocal
from app.models.company import Company, CompanyType
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem, POStatus
from app.models.sales_order import SalesOrder, SalesOrderItem, SOStatus
import uuid
from datetime import date, datetime

def seed_demo_data():
    db = SessionLocal()
    try:
        # 既にデータがあればスキップ
        if db.query(Company).count() > 0:
            return

        print("🌱 デモデータを投入中...")

        # ─── 仕入先 3社 ───────────────────────────────────────────
        suppliers = [
            Company(id=str(uuid.uuid4()), company_name="上海貿易株式会社", company_type=CompanyType.supplier,
                    country="中国", contact_name="王 明", contact_email="wang@shanghai-trade.cn", contact_phone="+86-21-1234-5678"),
            Company(id=str(uuid.uuid4()), company_name="Korea Parts Co., Ltd.", company_type=CompanyType.supplier,
                    country="韓国", contact_name="Kim Jisoo", contact_email="kim@koreaparts.kr", contact_phone="+82-2-9876-5432"),
            Company(id=str(uuid.uuid4()), company_name="Taiwan Supply Corp.", company_type=CompanyType.supplier,
                    country="台湾", contact_name="Chen Wei", contact_email="chen@twsupply.tw", contact_phone="+886-2-5555-1234"),
        ]
        for s in suppliers:
            db.add(s)
        db.flush()

        # ─── 得意先 10社 ──────────────────────────────────────────
        customers = [
            Company(id=str(uuid.uuid4()), company_name="東京商事株式会社", company_type=CompanyType.customer,
                    country="日本", contact_name="田中 太郎", contact_email="tanaka@tokyo-shoji.co.jp"),
            Company(id=str(uuid.uuid4()), company_name="大阪インポート株式会社", company_type=CompanyType.customer,
                    country="日本", contact_name="山田 花子", contact_email="yamada@osaka-import.co.jp"),
            Company(id=str(uuid.uuid4()), company_name="名古屋トレーディング", company_type=CompanyType.customer,
                    country="日本", contact_name="鈴木 一郎", contact_email="suzuki@nagoya-trading.co.jp"),
            Company(id=str(uuid.uuid4()), company_name="福岡物産株式会社", company_type=CompanyType.customer,
                    country="日本", contact_name="佐藤 次郎", contact_email="sato@fukuoka-bussan.co.jp"),
            Company(id=str(uuid.uuid4()), company_name="札幌商会", company_type=CompanyType.customer,
                    country="日本", contact_name="高橋 三郎", contact_email="takahashi@sapporo-shokai.co.jp"),
            Company(id=str(uuid.uuid4()), company_name="横浜インターナショナル", company_type=CompanyType.customer,
                    country="日本", contact_name="伊藤 四郎", contact_email="ito@yokohama-intl.co.jp"),
            Company(id=str(uuid.uuid4()), company_name="神戸マーチャント株式会社", company_type=CompanyType.customer,
                    country="日本", contact_name="渡辺 五郎", contact_email="watanabe@kobe-merchant.co.jp"),
            Company(id=str(uuid.uuid4()), company_name="仙台貿易株式会社", company_type=CompanyType.customer,
                    country="日本", contact_name="中村 六郎", contact_email="nakamura@sendai-trade.co.jp"),
            Company(id=str(uuid.uuid4()), company_name="広島エクスポート", company_type=CompanyType.customer,
                    country="日本", contact_name="小林 七郎", contact_email="kobayashi@hiroshima-export.co.jp"),
            Company(id=str(uuid.uuid4()), company_name="京都インポーター", company_type=CompanyType.customer,
                    country="日本", contact_name="加藤 八郎", contact_email="kato@kyoto-importer.co.jp"),
        ]
        for c in customers:
            db.add(c)
        db.flush()

        # ─── 商品マスタ 30種類 ────────────────────────────────────
        product_data = [
            ("SKU-001", "電子部品A（コンデンサ）", "Electronic Component A (Capacitor)", "8532.21", 150, "JPY", "個", 100, suppliers[0].id),
            ("SKU-002", "電子部品B（抵抗器）", "Electronic Component B (Resistor)", "8533.10", 80, "JPY", "個", 200, suppliers[0].id),
            ("SKU-003", "電子部品C（トランジスタ）", "Electronic Component C (Transistor)", "8541.21", 320, "JPY", "個", 50, suppliers[0].id),
            ("SKU-004", "プリント基板（小型）", "PCB Small", "8534.00", 2500, "JPY", "枚", 30, suppliers[0].id),
            ("SKU-005", "プリント基板（大型）", "PCB Large", "8534.00", 8000, "JPY", "枚", 20, suppliers[0].id),
            ("SKU-006", "液晶ディスプレイ 5inch", "LCD Display 5inch", "8524.11", 4500, "JPY", "個", 15, suppliers[1].id),
            ("SKU-007", "液晶ディスプレイ 10inch", "LCD Display 10inch", "8524.11", 12000, "JPY", "個", 10, suppliers[1].id),
            ("SKU-008", "タッチパネル", "Touch Panel", "8537.10", 6800, "JPY", "個", 10, suppliers[1].id),
            ("SKU-009", "バッテリーパック 3000mAh", "Battery Pack 3000mAh", "8507.60", 3200, "JPY", "個", 25, suppliers[1].id),
            ("SKU-010", "バッテリーパック 5000mAh", "Battery Pack 5000mAh", "8507.60", 5500, "JPY", "個", 20, suppliers[1].id),
            ("SKU-011", "ACアダプター 5V", "AC Adapter 5V", "8504.40", 1800, "JPY", "個", 30, suppliers[2].id),
            ("SKU-012", "ACアダプター 12V", "AC Adapter 12V", "8504.40", 2400, "JPY", "個", 25, suppliers[2].id),
            ("SKU-013", "USBケーブル Type-C", "USB Cable Type-C", "8544.42", 450, "JPY", "本", 100, suppliers[2].id),
            ("SKU-014", "HDMIケーブル 1m", "HDMI Cable 1m", "8544.42", 680, "JPY", "本", 80, suppliers[2].id),
            ("SKU-015", "HDMIケーブル 2m", "HDMI Cable 2m", "8544.42", 980, "JPY", "本", 60, suppliers[2].id),
            ("SKU-016", "アルミケース（小）", "Aluminum Case Small", "7612.90", 1200, "JPY", "個", 40, suppliers[0].id),
            ("SKU-017", "アルミケース（大）", "Aluminum Case Large", "7612.90", 2800, "JPY", "個", 20, suppliers[0].id),
            ("SKU-018", "プラスチックケース", "Plastic Case", "3923.10", 650, "JPY", "個", 50, suppliers[1].id),
            ("SKU-019", "冷却ファン 80mm", "Cooling Fan 80mm", "8414.59", 1500, "JPY", "個", 30, suppliers[1].id),
            ("SKU-020", "冷却ファン 120mm", "Cooling Fan 120mm", "8414.59", 2200, "JPY", "個", 20, suppliers[1].id),
            ("SKU-021", "ヒートシンク（小）", "Heat Sink Small", "8419.89", 800, "JPY", "個", 40, suppliers[2].id),
            ("SKU-022", "ヒートシンク（大）", "Heat Sink Large", "8419.89", 1800, "JPY", "個", 25, suppliers[2].id),
            ("SKU-023", "センサーモジュール（温度）", "Temperature Sensor Module", "9025.19", 2800, "JPY", "個", 20, suppliers[0].id),
            ("SKU-024", "センサーモジュール（湿度）", "Humidity Sensor Module", "9027.80", 3200, "JPY", "個", 15, suppliers[0].id),
            ("SKU-025", "Wi-Fiモジュール", "Wi-Fi Module", "8517.62", 4500, "JPY", "個", 15, suppliers[1].id),
            ("SKU-026", "Bluetoothモジュール", "Bluetooth Module", "8517.62", 3800, "JPY", "個", 20, suppliers[1].id),
            ("SKU-027", "マイクロコントローラー", "Microcontroller", "8542.31", 1200, "JPY", "個", 50, suppliers[2].id),
            ("SKU-028", "メモリチップ 4GB", "Memory Chip 4GB", "8542.32", 2800, "JPY", "個", 30, suppliers[2].id),
            ("SKU-029", "フラッシュストレージ 32GB", "Flash Storage 32GB", "8523.51", 3500, "JPY", "個", 25, suppliers[0].id),
            ("SKU-030", "電源基板", "Power Supply Board", "8504.40", 5500, "JPY", "枚", 15, suppliers[0].id),
        ]

        products = []
        for sku, name_ja, name_en, hs, price, currency, unit, min_stock, sup_id in product_data:
            p = Product(
                id=str(uuid.uuid4()),
                sku=sku,
                product_name=name_ja,
                product_name_en=name_en,
                hs_code=hs,
                unit_price=price,
                currency=currency,
                unit=unit,
                min_stock_qty=min_stock,
                supplier_id=sup_id,
            )
            db.add(p)
            products.append(p)
        db.flush()

        # ─── 在庫初期値 ───────────────────────────────────────────
        stock_levels = [250, 480, 120, 45, 28, 32, 18, 22, 55, 40,
                        75, 60, 320, 180, 140, 85, 35, 120, 65, 42,
                        90, 48, 38, 25, 30, 45, 150, 80, 60, 28]
        for p, qty in zip(products, stock_levels):
            inv = Inventory(id=str(uuid.uuid4()), product_id=p.id, quantity=qty)
            db.add(inv)
        db.flush()

        # ─── サンプル発注書 ───────────────────────────────────────
        po1 = PurchaseOrder(
            id=str(uuid.uuid4()),
            po_number="PO-202607-0001",
            supplier_id=suppliers[0].id,
            status=POStatus.ordered,
            order_date=date(2026, 7, 15),
            expected_date=date(2026, 8, 10),
            currency="JPY",
            payment_terms="T/T 30 days",
            total_amount=375000,
        )
        db.add(po1)
        db.flush()
        db.add(PurchaseOrderItem(id=str(uuid.uuid4()), purchase_order_id=po1.id,
            product_id=products[0].id, product_name=products[0].product_name,
            sku=products[0].sku, quantity=500, unit_price=150, amount=75000, unit="個"))
        db.add(PurchaseOrderItem(id=str(uuid.uuid4()), purchase_order_id=po1.id,
            product_id=products[3].id, product_name=products[3].product_name,
            sku=products[3].sku, quantity=50, unit_price=2500, amount=125000, unit="枚"))
        db.add(PurchaseOrderItem(id=str(uuid.uuid4()), purchase_order_id=po1.id,
            product_id=products[28].id, product_name=products[28].product_name,
            sku=products[28].sku, quantity=50, unit_price=3500, amount=175000, unit="個"))

        po2 = PurchaseOrder(
            id=str(uuid.uuid4()),
            po_number="PO-202607-0002",
            supplier_id=suppliers[1].id,
            status=POStatus.confirmed,
            order_date=date(2026, 7, 20),
            expected_date=date(2026, 8, 15),
            currency="JPY",
            payment_terms="L/C 60 days",
            total_amount=288000,
        )
        db.add(po2)
        db.flush()
        db.add(PurchaseOrderItem(id=str(uuid.uuid4()), purchase_order_id=po2.id,
            product_id=products[5].id, product_name=products[5].product_name,
            sku=products[5].sku, quantity=20, unit_price=4500, amount=90000, unit="個"))
        db.add(PurchaseOrderItem(id=str(uuid.uuid4()), purchase_order_id=po2.id,
            product_id=products[8].id, product_name=products[8].product_name,
            sku=products[8].sku, quantity=30, unit_price=3200, amount=96000, unit="個"))
        db.add(PurchaseOrderItem(id=str(uuid.uuid4()), purchase_order_id=po2.id,
            product_id=products[24].id, product_name=products[24].product_name,
            sku=products[24].sku, quantity=22, unit_price=4600, amount=101200, unit="個"))

        po3 = PurchaseOrder(
            id=str(uuid.uuid4()),
            po_number="PO-202607-0003",
            supplier_id=suppliers[2].id,
            status=POStatus.draft,
            order_date=date(2026, 7, 28),
            currency="JPY",
            payment_terms="T/T 30 days",
            total_amount=156000,
        )
        db.add(po3)
        db.flush()
        db.add(PurchaseOrderItem(id=str(uuid.uuid4()), purchase_order_id=po3.id,
            product_id=products[10].id, product_name=products[10].product_name,
            sku=products[10].sku, quantity=50, unit_price=1800, amount=90000, unit="個"))
        db.add(PurchaseOrderItem(id=str(uuid.uuid4()), purchase_order_id=po3.id,
            product_id=products[26].id, product_name=products[26].product_name,
            sku=products[26].sku, quantity=55, unit_price=1200, amount=66000, unit="個"))

        # ─── サンプル受注 ─────────────────────────────────────────
        so1 = SalesOrder(
            id=str(uuid.uuid4()),
            so_number="SO-202607-0001",
            customer_id=customers[0].id,
            status=SOStatus.confirmed,
            order_date=date(2026, 7, 10),
            delivery_date=date(2026, 8, 5),
            currency="JPY",
            payment_terms="T/T 30 days",
            destination="東京都千代田区",
            total_amount=520000,
        )
        db.add(so1)
        db.flush()
        db.add(SalesOrderItem(id=str(uuid.uuid4()), sales_order_id=so1.id,
            product_id=products[3].id, product_name=products[3].product_name,
            sku=products[3].sku, quantity=30, unit_price=3500, amount=105000, unit="枚"))
        db.add(SalesOrderItem(id=str(uuid.uuid4()), sales_order_id=so1.id,
            product_id=products[5].id, product_name=products[5].product_name,
            sku=products[5].sku, quantity=25, unit_price=6500, amount=162500, unit="個"))
        db.add(SalesOrderItem(id=str(uuid.uuid4()), sales_order_id=so1.id,
            product_id=products[24].id, product_name=products[24].product_name,
            sku=products[24].sku, quantity=28, unit_price=6500, amount=182000, unit="個"))
        db.add(SalesOrderItem(id=str(uuid.uuid4()), sales_order_id=so1.id,
            product_id=products[26].id, product_name=products[26].product_name,
            sku=products[26].sku, quantity=59, unit_price=1200, amount=70500, unit="個"))

        so2 = SalesOrder(
            id=str(uuid.uuid4()),
            so_number="SO-202607-0002",
            customer_id=customers[1].id,
            status=SOStatus.preparing,
            order_date=date(2026, 7, 18),
            delivery_date=date(2026, 8, 12),
            currency="JPY",
            payment_terms="L/C 60 days",
            destination="大阪府大阪市",
            total_amount=312000,
        )
        db.add(so2)
        db.flush()
        db.add(SalesOrderItem(id=str(uuid.uuid4()), sales_order_id=so2.id,
            product_id=products[6].id, product_name=products[6].product_name,
            sku=products[6].sku, quantity=15, unit_price=14000, amount=210000, unit="個"))
        db.add(SalesOrderItem(id=str(uuid.uuid4()), sales_order_id=so2.id,
            product_id=products[7].id, product_name=products[7].product_name,
            sku=products[7].sku, quantity=15, unit_price=6800, amount=102000, unit="個"))

        so3 = SalesOrder(
            id=str(uuid.uuid4()),
            so_number="SO-202607-0003",
            customer_id=customers[2].id,
            status=SOStatus.shipped,
            order_date=date(2026, 7, 5),
            delivery_date=date(2026, 7, 25),
            currency="JPY",
            payment_terms="T/T 30 days",
            destination="愛知県名古屋市",
            total_amount=198000,
        )
        db.add(so3)
        db.flush()
        db.add(SalesOrderItem(id=str(uuid.uuid4()), sales_order_id=so3.id,
            product_id=products[0].id, product_name=products[0].product_name,
            sku=products[0].sku, quantity=500, unit_price=180, amount=90000, unit="個"))
        db.add(SalesOrderItem(id=str(uuid.uuid4()), sales_order_id=so3.id,
            product_id=products[1].id, product_name=products[1].product_name,
            sku=products[1].sku, quantity=600, unit_price=90, amount=54000, unit="個"))
        db.add(SalesOrderItem(id=str(uuid.uuid4()), sales_order_id=so3.id,
            product_id=products[12].id, product_name=products[12].product_name,
            sku=products[12].sku, quantity=120, unit_price=450, amount=54000, unit="本"))

        db.commit()
        print("✅ デモデータ投入完了！")
        print(f"   仕入先: {len(suppliers)}社 / 得意先: {len(customers)}社")
        print(f"   商品: {len(products)}種類 / 発注書: 3件 / 受注: 3件")

    except Exception as e:
        db.rollback()
        print(f"⚠️  デモデータ投入エラー（既存データがある可能性）: {e}")
    finally:
        db.close()