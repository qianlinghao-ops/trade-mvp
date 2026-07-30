"""デモデータ投入スクリプト"""
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
        if db.query(Company).count() > 0:
            return
        print("🌱 デモデータを投入中...")
        suppliers = [
            Company(id=str(uuid.uuid4()), company_name="上海貿易株式会社", company_type=CompanyType.supplier, country="中国", contact_name="王 明", contact_email="wang@shanghai-trade.cn"),
            Company(id=str(uuid.uuid4()), company_name="Korea Parts Co., Ltd.", company_type=CompanyType.supplier, country="韓国", contact_name="Kim Jisoo", contact_email="kim@koreaparts.kr"),
            Company(id=str(uuid.uuid4()), company_name="Taiwan Supply Corp.", company_type=CompanyType.supplier, country="台湾", contact_name="Chen Wei", contact_email="chen@twsupply.tw"),
        ]
        for s in suppliers: db.add(s)
        db.flush()
        customers = [
            Company(id=str(uuid.uuid4()), company_name="東京商事株式会社", company_type=CompanyType.customer, country="日本", contact_name="田中 太郎"),
            Company(id=str(uuid.uuid4()), company_name="大阪インポート株式会社", company_type=CompanyType.customer, country="日本", contact_name="山田 花子"),
            Company(id=str(uuid.uuid4()), company_name="名古屋トレーディング", company_type=CompanyType.customer, country="日本", contact_name="鈴木 一郎"),
            Company(id=str(uuid.uuid4()), company_name="福岡物産株式会社", company_type=CompanyType.customer, country="日本", contact_name="佐藤 次郎"),
            Company(id=str(uuid.uuid4()), company_name="札幌商会", company_type=CompanyType.customer, country="日本", contact_name="高橋 三郎"),
            Company(id=str(uuid.uuid4()), company_name="横浜インターナショナル", company_type=CompanyType.customer, country="日本", contact_name="伊藤 四郎"),
            Company(id=str(uuid.uuid4()), company_name="神戸マーチャント株式会社", company_type=CompanyType.customer, country="日本", contact_name="渡辺 五郎"),
            Company(id=str(uuid.uuid4()), company_name="仙台貿易株式会社", company_type=CompanyType.customer, country="日本", contact_name="中村 六郎"),
            Company(id=str(uuid.uuid4()), company_name="広島エクスポート", company_type=CompanyType.customer, country="日本", contact_name="小林 七郎"),
            Company(id=str(uuid.uuid4()), company_name="京都インポーター", company_type=CompanyType.customer, country="日本", contact_name="加藤 八郎"),
        ]
        for c in customers: db.add(c)
        db.flush()
        product_data = [
            ("SKU-001","電子部品A（コンデンサ）","Electronic Component A",150,"JPY","個",100,suppliers[0].id),
            ("SKU-002","電子部品B（抵抗器）","Electronic Component B",80,"JPY","個",200,suppliers[0].id),
            ("SKU-003","電子部品C（トランジスタ）","Electronic Component C",320,"JPY","個",50,suppliers[0].id),
            ("SKU-004","プリント基板（小型）","PCB Small",2500,"JPY","枚",30,suppliers[0].id),
            ("SKU-005","プリント基板（大型）","PCB Large",8000,"JPY","枚",20,suppliers[0].id),
            ("SKU-006","液晶ディスプレイ 5inch","LCD Display 5inch",4500,"JPY","個",15,suppliers[1].id),
            ("SKU-007","液晶ディスプレイ 10inch","LCD Display 10inch",12000,"JPY","個",10,suppliers[1].id),
            ("SKU-008","タッチパネル","Touch Panel",6800,"JPY","個",10,suppliers[1].id),
            ("SKU-009","バッテリーパック 3000mAh","Battery Pack 3000mAh",3200,"JPY","個",25,suppliers[1].id),
            ("SKU-010","バッテリーパック 5000mAh","Battery Pack 5000mAh",5500,"JPY","個",20,suppliers[1].id),
            ("SKU-011","ACアダプター 5V","AC Adapter 5V",1800,"JPY","個",30,suppliers[2].id),
            ("SKU-012","ACアダプター 12V","AC Adapter 12V",2400,"JPY","個",25,suppliers[2].id),
            ("SKU-013","USBケーブル Type-C","USB Cable Type-C",450,"JPY","本",100,suppliers[2].id),
            ("SKU-014","HDMIケーブル 1m","HDMI Cable 1m",680,"JPY","本",80,suppliers[2].id),
            ("SKU-015","HDMIケーブル 2m","HDMI Cable 2m",980,"JPY","本",60,suppliers[2].id),
            ("SKU-016","アルミケース（小）","Aluminum Case Small",1200,"JPY","個",40,suppliers[0].id),
            ("SKU-017","アルミケース（大）","Aluminum Case Large",2800,"JPY","個",20,suppliers[0].id),
            ("SKU-018","プラスチックケース","Plastic Case",650,"JPY","個",50,suppliers[1].id),
            ("SKU-019","冷却ファン 80mm","Cooling Fan 80mm",1500,"JPY","個",30,suppliers[1].id),
            ("SKU-020","冷却ファン 120mm","Cooling Fan 120mm",2200,"JPY","個",20,suppliers[1].id),
            ("SKU-021","ヒートシンク（小）","Heat Sink Small",800,"JPY","個",40,suppliers[2].id),
            ("SKU-022","ヒートシンク（大）","Heat Sink Large",1800,"JPY","個",25,suppliers[2].id),
            ("SKU-023","センサーモジュール（温度）","Temperature Sensor",2800,"JPY","個",20,suppliers[0].id),
            ("SKU-024","センサーモジュール（湿度）","Humidity Sensor",3200,"JPY","個",15,suppliers[0].id),
            ("SKU-025","Wi-Fiモジュール","Wi-Fi Module",4500,"JPY","個",15,suppliers[1].id),
            ("SKU-026","Bluetoothモジュール","Bluetooth Module",3800,"JPY","個",20,suppliers[1].id),
            ("SKU-027","マイクロコントローラー","Microcontroller",1200,"JPY","個",50,suppliers[2].id),
            ("SKU-028","メモリチップ 4GB","Memory Chip 4GB",2800,"JPY","個",30,suppliers[2].id),
            ("SKU-029","フラッシュストレージ 32GB","Flash Storage 32GB",3500,"JPY","個",25,suppliers[0].id),
            ("SKU-030","電源基板","Power Supply Board",5500,"JPY","枚",15,suppliers[0].id),
        ]
        products = []
        for sku,name_ja,name_en,price,currency,unit,min_stock,sup_id in product_data:
            p = Product(id=str(uuid.uuid4()), sku=sku, product_name=name_ja, product_name_en=name_en, unit_price=price, currency=currency, unit=unit, min_stock_qty=min_stock, supplier_id=sup_id)
            db.add(p); products.append(p)
        db.flush()
        stock_levels = [250,480,120,45,28,32,18,22,55,40,75,60,320,180,140,85,35,120,65,42,90,48,38,25,30,45,150,80,60,28]
        for p, qty in zip(products, stock_levels):
            db.add(Inventory(id=str(uuid.uuid4()), product_id=p.id, quantity=qty))
        db.flush()
        po1 = PurchaseOrder(id=str(uuid.uuid4()), po_number="PO-202607-0001", supplier_id=suppliers[0].id, status=POStatus.ordered, order_date=date(2026,7,15), expected_date=date(2026,8,10), currency="JPY", payment_terms="T/T 30 days", total_amount=375000)
        db.add(po1); db.flush()
        db.add(PurchaseOrderItem(id=str(uuid.uuid4()), purchase_order_id=po1.id, product_id=products[0].id, product_name=products[0].product_name, sku=products[0].sku, quantity=500, unit_price=150, amount=75000, unit="個"))
        db.add(PurchaseOrderItem(id=str(uuid.uuid4()), purchase_order_id=po1.id, product_id=products[3].id, product_name=products[3].product_name, sku=products[3].sku, quantity=50, unit_price=2500, amount=125000, unit="枚"))
        so1 = SalesOrder(id=str(uuid.uuid4()), so_number="SO-202607-0001", customer_id=customers[0].id, status=SOStatus.confirmed, order_date=date(2026,7,10), delivery_date=date(2026,8,5), currency="JPY", payment_terms="T/T 30 days", destination="東京都千代田区", total_amount=520000)
        db.add(so1); db.flush()
        db.add(SalesOrderItem(id=str(uuid.uuid4()), sales_order_id=so1.id, product_id=products[3].id, product_name=products[3].product_name, sku=products[3].sku, quantity=30, unit_price=3500, amount=105000, unit="枚"))
        db.commit()
        print("✅ デモデータ投入完了！")
    except Exception as e:
        db.rollback()
        print(f"⚠️ デモデータ投入エラー: {e}")
    finally:
        db.close()
