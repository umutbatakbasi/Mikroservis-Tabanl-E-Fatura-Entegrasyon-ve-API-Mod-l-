# Mikroservis Tabanlı E-Fatura Entegrasyon ve API Modülü

Bu proje, modern bir ERP sisteminin temel faturalama süreçlerini simüle eden, RESTful API üzerinden **Müşteri (Customer)**, **Ürün (Product)** ve **Fatura (Invoice)** işlemlerini gerçekleştiren ve kurumsal düzeyde **GİB (Gelir İdaresi Başkanlığı) / Özel Entegratör** E-Fatura servisleriyle entegre olabilecek şekilde tasarlanmış profesyonel bir backend uygulamasıdır.

---

## İçindekiler
- [Proje Amacı ve Özellikler](#proje-amacı-ve-özellikler)
- [Kullanılan Teknolojiler](#kullanılan-teknolojiler)
- [Mimari ve Tasarım Prensipleri](#mimari-ve-tasarım-prensipleri)
- [Klasör Yapısı](#klasör-yapısı)
- [Veritabanı Tasarımı ve İlişkiler](#veritabanı-tasarımı-ve-ilişkiler)
- [Kurulum ve Çalıştırma](#kurulum-ve-çalıştırma)
  - [1. Sanal Ortam (Virtualenv) Oluşturma](#1-sanal-ortam-virtualenv-oluşturma)
  - [2. Bağımlılıkların Kurulumu](#2-bağımlılıkların-kurulumu)
  - [3. Çevre Değişkenleri (.env)](#3-çevre-değişkenleri-env)
  - [4. Veritabanı Migrasyonları (Alembic)](#4-veritabanı-migrasyonları-alembic)
  - [5. Örnek Verilerin Yüklenmesi (Seed Data)](#5-örnek-verilerin-yüklenmesi-seed-data)
  - [6. Uygulamanın Başlatılması](#6-uygulamanın-başlatılması)
- [API Dokümantasyonu ve Endpointler](#api-dokümantasyonu-ve-endpointler)
- [Örnek İstek ve Yanıtlar](#örnek-istek-ve-yanıtlar)
- [E-Fatura Entegrasyon Mimarisi ve Gelecek Yol Haritası](#e-fatura-entegrasyon-mimarisi-ve-gelecek-yol-haritası)
- [Testlerin Çalıştırılması](#testlerin-çalıştırılması)

---

## Proje Amacı ve Özellikler

1. **Katmanlı Kurumsal Mimari**: Router, Service, Repository, Model ve Schema katmanlarının tam izolasyonu.
2. **Güvenilir Fatura Hesaplama Mantığı**: Müşteri tarafından gönderilen toplam tutarlar kabul edilmez; birim fiyatlar ve KDV oranları veritabanındaki ürün kayıtlarından alınarak satır ve dip toplamlar arka planda transaction güvencesiyle hesaplanır.
3. **Otomatik ve Sıralı Fatura Numarası Üretimi**: Fatura tarihinin yılına göre çakışmasız ve sıralı numaralandırma (Örn: `INV-2026-000001`).
4. **Normalizasyon ve Veri Bütünlüğü**: En az 3NF kuralına uygun veritabanı tasarımı; Check Constraint'ler, Unique ve Foreign Key kısıtlamaları.
5. **E-Fatura Abstraction Mimarisi**: Mock ve gerçek GİB/Özel Entegratör servislerinin `BaseEInvoiceService` soyutlaması üzerinden tak-çıkar (pluggable) şekilde çalışabilmesi.
6. **Kapsamlı Test Kapsamı**: İzole test veritabanı üzerinde 18 farklı birim ve entegrasyon test senaryosu.

---

## Kullanılan Teknolojiler

* **Python 3.12+** (Python 3.14 ile tam uyumlu)
* **FastAPI**: Yüksek performanslı modern asenkron web framework'ü
* **Uvicorn**: ASGI web sunucusu
* **SQLAlchemy 2.x**: Modern `Mapped` / `mapped_column` sözdizimli ORM
* **Pydantic v2 & Pydantic Settings**: Tip güvenliği, veri doğrulama ve konfigürasyon yönetimi
* **SQLite**: Yerel geliştirme ve test ortamı (PostgreSQL/MySQL uyumlu)
* **Alembic**: Veritabanı şema versiyonlama ve migrasyon aracı
* **python-dotenv**: Ortam değişkenleri yönetimi
* **pytest & HTTPX**: Uçtan uca ve birim testler
* **Swagger UI & ReDoc**: Otomatik interaktif API dokümantasyonu

---

## Mimari ve Tasarım Prensipleri

Uygulama, **Sorumlulukların Ayrılığı (Separation of Concerns)** ve **Temiz Mimari (Clean Architecture)** ilkelerine göre inşa edilmiştir:

* **`Routers`**: HTTP isteklerini karşılar, parametreleri doğrular ve servis katmanına iletir.
* **`Services`**: İş mantığını (business logic), fatura matematiksel hesaplamalarını, E-Fatura entegrasyonunu ve transaction yönetimini yürütür.
* **`Repositories`**: Doğrudan veritabanı sorgularını (SQLAlchemy 2.x) soyutlar.
* **`Models`**: Veritabanı tablolarını, indeksleri ve ilişkileri tanımlar.
* **`Schemas`**: API istek/yanıt modellerini Pydantic ile doğrular.
* **`Core`**: Yapılandırma (`config.py`) ve oturum yönetimini (`database.py`) üstlenir.

---

## Klasör Yapısı

```text
Staj projesi/
│
├── app/
│   ├── main.py                     # FastAPI uygulama yapılandırması & middleware
│   │
│   ├── core/
│   │   ├── config.py               # Pydantic BaseSettings konfigürasyonu
│   │   └── database.py             # SQLAlchemy 2.0 Engine & SessionLocal
│   │
│   ├── models/
│   │   ├── customer.py             # Customers ORM modeli
│   │   ├── product.py              # Products ORM modeli
│   │   ├── invoice_header.py       # InvoiceHeaders ORM modeli & Status enum
│   │   └── invoice_line.py         # InvoiceLines ORM modeli
│   │
│   ├── schemas/
│   │   ├── customer.py             # Customer Pydantic v2 DTO'ları
│   │   ├── product.py              # Product Pydantic v2 DTO'ları
│   │   └── invoice.py              # Invoice & Line Pydantic v2 DTO'ları
│   │
│   ├── repositories/
│   │   ├── customer_repository.py  # Müşteri veritabanı işlemleri
│   │   ├── product_repository.py   # Ürün veritabanı işlemleri
│   │   └── invoice_repository.py   # Fatura veritabanı işlemleri
│   │
│   ├── services/
│   │   ├── customer_service.py     # Müşteri iş mantığı
│   │   ├── product_service.py      # Ürün iş mantığı
│   │   ├── invoice_service.py      # Fatura hesaplama, numara üretimi & transaction
│   │   └── einvoice_service.py     # E-Fatura servis soyutlaması & Mock servis
│   │
│   └── routers/
│       ├── customers.py            # /api/customers endpointleri
│       ├── products.py             # /api/products endpointleri
│       └── invoices.py             # /api/invoices endpointleri
│
├── tests/
│   ├── conftest.py                 # İzole TestClient ve in-memory DB fixture'ları
│   ├── test_customers.py           # Müşteri CRUD ve doğrulama testleri
│   ├── test_products.py            # Ürün CRUD ve doğrulama testleri
│   └── test_invoices.py            # Fatura oluşturma, hesaplama, gönderim testleri
│
├── alembic/
│   ├── versions/                   # Veritabanı migrasyon dosyaları
│   └── env.py                      # Alembic migrasyon konfigürasyonu
│
├── .env                            # Yerel ortam değişkenleri
├── .env.example                    # Örnek çevre değişkenleri şablonu
├── .gitignore                      # Git takip dışı dosyalar
├── alembic.ini                     # Alembic ana yapılandırma dosyası
├── pytest.ini                      # Pytest konfigürasyonu
├── requirements.txt                # Python paket bağımlılıkları
├── run.py                          # Uvicorn sunucu başlatıcı
├── seed.py                         # Örnek veri yükleme scripti
└── README.md                       # Kapsamlı proje dokümantasyonu
```

---

## Veritabanı Tasarımı ve İlişkiler

```mermaid
erDiagram
    CUSTOMERS ||--o{ INVOICE_HEADERS : "has many"
    INVOICE_HEADERS ||--|{ INVOICE_LINES : "contains"
    PRODUCTS ||--o{ INVOICE_LINES : "referenced in"

    CUSTOMERS {
        int id PK
        string tax_number UK "VKN / TCKN"
        string name "Zorunlu"
        string email
        string phone
        string address
        datetime created_at
    }

    PRODUCTS {
        int id PK
        string code UK "Ürün Kodu"
        string name "Zorunlu"
        string description
        numeric unit_price ">= 0"
        numeric vat_rate "0-100"
        datetime created_at
    }

    INVOICE_HEADERS {
        int id PK
        string invoice_number UK "Örn: INV-2026-000001"
        int customer_id FK
        date invoice_date
        numeric total_amount "Ara Toplam"
        numeric total_vat "Toplam KDV"
        numeric grand_total "Genel Toplam"
        string status "DRAFT, SENT, ACCEPTED, REJECTED"
        string uuid "E-Fatura UUID (ETTN)"
        datetime created_at
    }

    INVOICE_LINES {
        int id PK
        int invoice_id FK
        int product_id FK
        numeric quantity "> 0"
        numeric unit_price
        numeric vat_rate
        numeric line_total "quantity * unit_price"
        numeric vat_amount "line_total * vat_rate / 100"
    }
```

---

## Kurulum ve Çalıştırma

### 1. Sanal Ortam (Virtualenv) Oluşturma

PowerShell terminalini açarak proje dizininde sanal ortamı oluşturun:

```powershell
python -m venv .venv
```

Sanal ortamı aktifleştirin:

```powershell
.\.venv\Scripts\Activate.ps1
```

*(Eğer execution policy uyarısı alırsanız `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` komutunu çalıştırabilirsiniz.)*

### 2. Bağımlılıkların Kurulumu

```powershell
pip install -r requirements.txt
```

### 3. Çevre Değişkenleri (.env)

`.env.example` dosyasını temel alarak `.env` dosyasını doğrulayın:

```ini
APP_NAME="E-Invoice Integration API"
APP_VERSION="1.0.0"
API_V1_PREFIX="/api"
DEBUG=True
DATABASE_URL="sqlite:///./invoice.db"
INVOICE_NUMBER_PREFIX="INV"
```

### 4. Veritabanı Migrasyonları (Alembic)

Veritabanı tablolarını Alembic migrasyonu ile oluşturmak için:

```powershell
alembic upgrade head
```

### 5. Örnek Verilerin Yüklenmesi (Seed Data)

Sisteme 3 müşteri, 5 ürün ve 2 hazır hesaplanmış fatura yüklemek için:

```powershell
python seed.py
```

### 6. Uygulamanın Başlatılması

Geliştirme sunucusunu başlatmak için:

```powershell
python run.py
```

Alternatif olarak doğrudan uvicorn ile:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Sunucu `http://127.0.0.1:8000` adresinde çalışmaya başlayacaktır.

---

## API Dokümantasyonu ve Endpointler

Uygulama çalışırken aşağıdaki adreslerden interaktif dokümantasyona erişebilirsiniz:

* **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Endpoint Listesi

| Modül | Metod | Endpoint | Açıklama | Başarılı Kod |
| :--- | :--- | :--- | :--- | :--- |
| **Customers** | `POST` | `/api/customers` | Yeni müşteri oluştur | `201 Created` |
| | `GET` | `/api/customers` | Tüm müşterileri listele | `200 OK` |
| | `GET` | `/api/customers/{id}` | Müşteri detayını getir | `200 OK` |
| | `PUT` | `/api/customers/{id}` | Müşteri bilgilerini güncelle | `200 OK` |
| | `DELETE` | `/api/customers/{id}` | Müşteriyi sil | `204 No Content` |
| **Products** | `POST` | `/api/products` | Yeni ürün oluştur | `201 Created` |
| | `GET` | `/api/products` | Tüm ürünleri listele | `200 OK` |
| | `GET` | `/api/products/{id}` | Ürün detayını getir | `200 OK` |
| | `PUT` | `/api/products/{id}` | Ürünü güncelle | `200 OK` |
| | `DELETE` | `/api/products/{id}` | Ürünü sil | `204 No Content` |
| **Invoices** | `POST` | `/api/invoices` | Yeni fatura oluştur (asenkron, backend hesaplamalı) | `201 Created` |
| | `GET` | `/api/invoices` | Faturaları listele (durum, müşteri ve tarih filtresi) | `200 OK` |
| | `GET` | `/api/invoices/{id}` | Fatura detayını ve kalemlerini getir | `200 OK` |
| | `PUT` | `/api/invoices/{id}` | Taslak faturayı güncelle (DRAFT kontrollü) | `200 OK` |
| | `GET` | `/api/invoices/{id}/lines` | Sadece fatura kalemlerini getir | `200 OK` |
| | `DELETE` | `/api/invoices/{id}` | Faturayı sil | `204 No Content` |
| | `POST` | `/api/invoices/{id}/send` | E-Fatura sistemine gönder | `200 OK` |
| | `GET` | `/api/invoices/{id}/ubl` | UBL-TR 1.2 veri paketi (JSON/XML) | `200 OK` |
| | `GET` | `/api/invoices/{id}/xml` | UBL-TR 1.2 XML belgesi (`application/xml`) | `200 OK` |

---

## Örnek İstek ve Yanıtlar

### 1. Yeni Fatura Oluşturma (POST `/api/invoices`)

**İstek Gövdesi (Payload):**
```json
{
  "customer_id": 1,
  "invoice_date": "2026-09-25",
  "lines": [
    {
      "product_id": 1,
      "quantity": 2
    },
    {
      "product_id": 2,
      "quantity": 1
    }
  ]
}
```

*Not: İstemci fiyat ve toplam tutar göndermez. Backend veritabanından ürünün birim fiyatını (2.500,00 TL) ve KDV oranını (%20) alır.*

**Dönen Yanıt (`201 Created`):**
```json
{
  "id": 1,
  "invoice_number": "INV-2026-000001",
  "customer_id": 1,
  "invoice_date": "2026-09-25",
  "total_amount": "12500.00",
  "total_vat": "2500.00",
  "grand_total": "15000.00",
  "status": "DRAFT",
  "uuid": null,
  "created_at": "2026-09-25T15:11:35",
  "lines": [
    {
      "id": 1,
      "invoice_id": 1,
      "product_id": 1,
      "quantity": "2.00",
      "unit_price": "2500.00",
      "vat_rate": "20.00",
      "line_total": "5000.00",
      "vat_amount": "1000.00"
    },
    {
      "id": 2,
      "invoice_id": 1,
      "product_id": 2,
      "quantity": "1.00",
      "unit_price": "7500.00",
      "vat_rate": "20.00",
      "line_total": "7500.00",
      "vat_amount": "1500.00"
    }
  ]
}
```

### 2. Faturayı E-Fatura Servisine Gönderme (POST `/api/invoices/{id}/send`)

**Dönen Yanıt (`200 OK`):**
```json
{
  "success": true,
  "message": "Fatura GİB sistemine başarıyla iletildi ve 'ACCEPTED' olarak onaylandı.",
  "invoice_id": 1,
  "invoice_number": "INV-2026-000001",
  "uuid": "1c509840-b880-404e-800b-3bbe6ef59d24",
  "status": "ACCEPTED"
}
```

### 3. Faturanın UBL-TR 1.2 XML Belgesini Alma (GET `/api/invoices/{id}/xml`)

**Yanıt Başlığı:** `Content-Type: application/xml`  
**Dönen Yanıt (`200 OK` - XML Çıktısı):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>TR1.2</cbc:CustomizationID>
    <cbc:ProfileID>TICARIFATURA</cbc:ProfileID>
    <cbc:ID>INV-2026-000001</cbc:ID>
    <cbc:UUID>1c509840-b880-404e-800b-3bbe6ef59d24</cbc:UUID>
    <cbc:IssueDate>2026-09-25</cbc:IssueDate>
    <cbc:InvoiceTypeCode>SATIS</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>TRY</cbc:DocumentCurrencyCode>
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="VKN">1234567890</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name>ERP E-Dönüşüm ve Bilişim Hizmetleri A.Ş.</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>Büyükdere Cad. No:199</cbc:StreetName>
                <cbc:CitySubdivisionName>Sarıyer</cbc:CitySubdivisionName>
                <cbc:CityName>İstanbul</cbc:CityName>
            </cac:PostalAddress>
        </cac:Party>
    </cac:AccountingSupplierParty>
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="VKN">1234567890</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name>Atlas Yazılım ve Danışmanlık A.Ş.</cbc:Name>
            </cac:PartyName>
        </cac:Party>
    </cac:AccountingCustomerParty>
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="TRY">2500.00</cbc:TaxAmount>
    </cac:TaxTotal>
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="TRY">12500.00</cbc:LineExtensionAmount>
        <cbc:PayableAmount currencyID="TRY">15000.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    <cac:InvoiceLine>
        <cbc:ID>1</cbc:ID>
        <cbc:InvoicedQuantity unitCode="NIU">2.00</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="TRY">5000.00</cbc:LineExtensionAmount>
        ...
    </cac:InvoiceLine>
</Invoice>
```

---

## E-Fatura Entegrasyon Mimarisi ve Gelecek Yol Haritası

Sistem, **Dependency Injection** ve **Strategy / Adapter Tasarım Deseni** ile tasarlanmıştır.

`app/services/einvoice_service.py` ve `app/services/ubl_service.py` içerisinde:

* **`UBLTRService`**: `xml.etree.ElementTree` kütüphanesini kullanarak nesneleri UBL-TR 1.2 XML ağacına serileştirir.
* **`BaseEInvoiceService`**: Entegratör ve GİB servis çağrılarını soyutlar.

---

## Testlerin Çalıştırılması

Proje, tüm uç noktaları, XML dönüşümünü ve sınır durumları test eden 30 adet senaryoyu içerir:

* Müşteri oluşturma, listeleme, güncelleme ve silme
* Tekil Vergi Numarası (`tax_number`) çakışma kontrolü (409)
* Ürün oluşturma, listeleme, güncelleme ve silme
* Tekil Ürün Kodu (`code`) çakışma kontrolü (409)
* Negatif birim fiyat ve hatalı KDV doğrulama kontrolleri (422)
* Otomatik fatura numaralandırma doğrulaması
* Fatura satır toplamı, KDV ve genel toplam matematiksel hesaplama doğrulaması
* Olmayan müşteri ve ürünle fatura oluşturulmasının engellenmesi (404)
* Taslak fatura güncelleme (`PUT /invoices/{id}`) ve onaylı fatura koruması (400)
* Entegratör filtreleme parametreleri sorgu testleri
* Faturanın E-Fatura servisine gönderilmesi ve durum güncellemesi
* VKN (10 hane) / TCKN (11 hane) doğrulama testleri
* UBL-TR 1.2 XML ElementTree şema doğrulaması ve `/invoices/{id}/xml` uç nokta testleri

Testleri çalıştırmak için:

```powershell
pytest -v
```

Çıktı Örneği:
```text
======================= 30 passed in 0.95s =======================
```

---

## Lisans & Geliştirici Notu

Bu proje kurumsal standartlarda, temiz kod prensiplerine (Clean Code & SOLID) ve modern Python (3.12+) en iyi pratiklerine tam uyumlu olarak geliştirilmiştir.

