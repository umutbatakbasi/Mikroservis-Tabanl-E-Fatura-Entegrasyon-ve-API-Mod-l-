"""Seed script to populate initial sample data:
- 3 Customers
- 5 Products
- 2 Invoices with lines and calculations
"""
from datetime import date
from decimal import Decimal
from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.product import Product
from app.models.invoice_header import InvoiceHeader
from app.schemas.customer import CustomerCreate
from app.schemas.product import ProductCreate
from app.schemas.invoice import InvoiceCreate, InvoiceLineCreate
from app.services.customer_service import CustomerService
from app.services.product_service import ProductService
from app.services.invoice_service import InvoiceService


def seed_data():
    db = SessionLocal()
    customer_service = CustomerService()
    product_service = ProductService()
    invoice_service = InvoiceService()

    print("--- Veritabanı Örnek Veri Yükleme (Seed) Başlatılıyor ---")

    try:
        # 1. Customers
        sample_customers = [
            CustomerCreate(
                tax_number="1234567890",
                name="Atlas Yazılım ve Danışmanlık A.Ş.",
                email="muhasebe@atlasyazilim.com",
                phone="+90 212 400 1010",
                address="Maslak Mah. Büyükdere Cad. No:42 Sarıyer / İstanbul"
            ),
            CustomerCreate(
                tax_number="9876543210",
                name="Kuzey Lojistik ve Ticaret Ltd. Şti.",
                email="finans@kuzeylojistik.com",
                phone="+90 216 300 2020",
                address="Batı Ataşehir Barbaros Mah. No:15 Ataşehir / İstanbul"
            ),
            CustomerCreate(
                tax_number="1122334455",
                name="Ege Global Dağıtım A.Ş.",
                email="fatura@egeglobal.com",
                phone="+90 232 200 3030",
                address="Alsancak Liman Cad. No:8 Konak / İzmir"
            ),
        ]

        created_customers = []
        for cust_in in sample_customers:
            existing = customer_service.repository.get_by_tax_number(db, cust_in.tax_number)
            if not existing:
                c = customer_service.create_customer(db, cust_in)
                print(f"[OK] Müşteri oluşturuldu: {c.name} (VKN: {c.tax_number})")
                created_customers.append(c)
            else:
                print(f"[MEVCUT] Müşteri zaten var: {existing.name}")
                created_customers.append(existing)

        # 2. Products
        sample_products = [
            ProductCreate(
                code="SRV-001",
                name="ERP Bulut Sunucu Barındırma (Aylık)",
                description="Yüksek erişilebilirlikli 8 vCPU 32GB RAM bulut sunucu",
                unit_price=Decimal("2500.00"),
                vat_rate=Decimal("20.00")
            ),
            ProductCreate(
                code="LIC-002",
                name="E-Fatura Entegratör Kullanıcı Lisansı (Yıllık)",
                description="GİB uyumlu e-fatura ve e-arşiv gönderim lisansı",
                unit_price=Decimal("7500.00"),
                vat_rate=Decimal("20.00")
            ),
            ProductCreate(
                code="CNS-003",
                name="Teknik Danışmanlık ve Eğitim Hizmeti (Saatlik)",
                description="Kıdemli yazılım mimarı danışmanlık saati",
                unit_price=Decimal("1800.00"),
                vat_rate=Decimal("20.00")
            ),
            ProductCreate(
                code="DEV-004",
                name="Özel API Entegrasyon Paketi",
                description="REST API uç nokta geliştirme ve test paketi",
                unit_price=Decimal("12000.00"),
                vat_rate=Decimal("20.00")
            ),
            ProductCreate(
                code="SUP-005",
                name="7/24 SLA Destek Paketi (Aylık)",
                description="Kritik seviye kurumsal destek ve izleme",
                unit_price=Decimal("4500.00"),
                vat_rate=Decimal("20.00")
            ),
        ]

        created_products = []
        for prod_in in sample_products:
            existing = product_service.repository.get_by_code(db, prod_in.code)
            if not existing:
                p = product_service.create_product(db, prod_in)
                print(f"[OK] Ürün oluşturuldu: {p.name} (Kod: {p.code}, Fiyat: {p.unit_price} TL)")
                created_products.append(p)
            else:
                print(f"[MEVCUT] Ürün zaten var: {existing.name}")
                created_products.append(existing)

        # 3. Invoices
        existing_invoices = invoice_service.get_all_invoices(db)
        if len(existing_invoices) < 2:
            # Invoice 1
            inv1_payload = InvoiceCreate(
                customer_id=created_customers[0].id,
                invoice_date=date.today(),
                lines=[
                    InvoiceLineCreate(product_id=created_products[0].id, quantity=Decimal("2.00")),
                    InvoiceLineCreate(product_id=created_products[1].id, quantity=Decimal("1.00")),
                ]
            )
            inv1 = invoice_service.create_invoice(db, inv1_payload)
            print(f"[OK] 1. Fatura oluşturuldu: No: {inv1.invoice_number}, Toplam: {inv1.grand_total} TL")

            # Invoice 2
            inv2_payload = InvoiceCreate(
                customer_id=created_customers[1].id,
                invoice_date=date.today(),
                lines=[
                    InvoiceLineCreate(product_id=created_products[2].id, quantity=Decimal("5.00")),
                    InvoiceLineCreate(product_id=created_products[4].id, quantity=Decimal("1.00")),
                ]
            )
            inv2 = invoice_service.create_invoice(db, inv2_payload)
            print(f"[OK] 2. Fatura oluşturuldu: No: {inv2.invoice_number}, Toplam: {inv2.grand_total} TL")
        else:
            print("[MEVCUT] Sistemde zaten yeterli örnek fatura mevcut.")

        print("--- Örnek Veri Yükleme Başarıyla Tamamlandı! ---")

    except Exception as e:
        print(f"[HATA] Seed işlemi sırasında hata: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
