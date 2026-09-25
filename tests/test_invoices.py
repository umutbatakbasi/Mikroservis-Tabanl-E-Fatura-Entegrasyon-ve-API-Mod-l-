from datetime import date
from decimal import Decimal
from fastapi import status


def create_sample_customer_and_products(client):
    """Helper fixture setup for creating a customer and two products."""
    cust_res = client.post("/api/customers", json={
        "tax_number": "1112223334",
        "name": "Fatura Müşterisi A.Ş.",
        "email": "fatura@musteri.com"
    })
    customer_id = cust_res.json()["id"]

    prod1_res = client.post("/api/products", json={
        "code": "PROD-INV-1",
        "name": "Ürün 1",
        "unit_price": 1000.00,
        "vat_rate": 20.00
    })
    prod1_id = prod1_res.json()["id"]

    prod2_res = client.post("/api/products", json={
        "code": "PROD-INV-2",
        "name": "Ürün 2",
        "unit_price": 500.00,
        "vat_rate": 10.00
    })
    prod2_id = prod2_res.json()["id"]

    return customer_id, prod1_id, prod2_id


def test_create_invoice_and_calculate_totals(client):
    """
    Scenario 5 & 6:
    - Invoice oluşturma
    - Invoice toplamlarının backend tarafından doğru hesaplanması
      Line 1: 2 adet * 1000.00 = 2000.00 TL (%20 KDV = 400.00 TL)
      Line 2: 3 adet * 500.00 = 1500.00 TL (%10 KDV = 150.00 TL)
      Total Amount (Ara toplam) = 3500.00 TL
      Total VAT (Toplam KDV)   = 550.00 TL
      Grand Total (Genel Toplam)= 4050.00 TL
    """
    customer_id, prod1_id, prod2_id = create_sample_customer_and_products(client)

    payload = {
        "customer_id": customer_id,
        "invoice_date": str(date.today()),
        "lines": [
            {"product_id": prod1_id, "quantity": 2},
            {"product_id": prod2_id, "quantity": 3}
        ]
    }

    response = client.post("/api/invoices", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["id"] is not None
    assert data["invoice_number"].startswith(f"INV-{date.today().year}-")
    assert data["customer_id"] == customer_id
    assert Decimal(str(data["total_amount"])) == Decimal("3500.00")
    assert Decimal(str(data["total_vat"])) == Decimal("550.00")
    assert Decimal(str(data["grand_total"])) == Decimal("4050.00")
    assert data["status"] == "DRAFT"

    # Line item checks
    lines = data["lines"]
    assert len(lines) == 2

    line1 = next(l for l in lines if l["product_id"] == prod1_id)
    assert Decimal(str(line1["quantity"])) == Decimal("2.00")
    assert Decimal(str(line1["unit_price"])) == Decimal("1000.00")
    assert Decimal(str(line1["vat_rate"])) == Decimal("20.00")
    assert Decimal(str(line1["line_total"])) == Decimal("2000.00")
    assert Decimal(str(line1["vat_amount"])) == Decimal("400.00")

    line2 = next(l for l in lines if l["product_id"] == prod2_id)
    assert Decimal(str(line2["quantity"])) == Decimal("3.00")
    assert Decimal(str(line2["unit_price"])) == Decimal("500.00")
    assert Decimal(str(line2["vat_rate"])) == Decimal("10.00")
    assert Decimal(str(line2["line_total"])) == Decimal("1500.00")
    assert Decimal(str(line2["vat_amount"])) == Decimal("150.00")


def test_create_invoice_nonexistent_customer(client):
    """Scenario 7: Olmayan customer ile invoice oluşturulamaması."""
    _, prod1_id, _ = create_sample_customer_and_products(client)

    payload = {
        "customer_id": 99999,  # Non-existent customer ID
        "invoice_date": str(date.today()),
        "lines": [{"product_id": prod1_id, "quantity": 1}]
    }
    response = client.post("/api/invoices", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Customer with ID 99999 not found" in response.json()["detail"]


def test_create_invoice_nonexistent_product(client):
    """Scenario 8: Olmayan product ile invoice oluşturulamaması."""
    customer_id, _, _ = create_sample_customer_and_products(client)

    payload = {
        "customer_id": customer_id,
        "invoice_date": str(date.today()),
        "lines": [{"product_id": 88888, "quantity": 1}]  # Non-existent product ID
    }
    response = client.post("/api/invoices", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Product with ID 88888 not found" in response.json()["detail"]


def test_send_invoice(client):
    """Scenario 11: Invoice gönderme (E-Fatura servis entegrasyonu)."""
    customer_id, prod1_id, _ = create_sample_customer_and_products(client)

    # 1. Create invoice in DRAFT
    create_res = client.post("/api/invoices", json={
        "customer_id": customer_id,
        "invoice_date": str(date.today()),
        "lines": [{"product_id": prod1_id, "quantity": 1}]
    })
    invoice_id = create_res.json()["id"]
    assert create_res.json()["status"] == "DRAFT"

    # 2. Send invoice
    send_res = client.post(f"/api/invoices/{invoice_id}/send")
    assert send_res.status_code == status.HTTP_200_OK
    send_data = send_res.json()
    assert send_data["success"] is True
    assert send_data["invoice_id"] == invoice_id
    assert send_data["status"] == "ACCEPTED"
    assert len(send_data["uuid"]) > 0

    # 3. Verify invoice record updated
    get_res = client.get(f"/api/invoices/{invoice_id}")
    assert get_res.json()["status"] == "ACCEPTED"
    assert get_res.json()["uuid"] == send_data["uuid"]


def test_invoice_not_found_404(client):
    """Scenario 12: Invoice bulunamadığında 404."""
    response = client.get("/api/invoices/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Invoice with ID 99999 not found" in response.json()["detail"]


def test_get_invoice_lines_and_delete(client):
    """Test retrieving lines separately and invoice deletion."""
    customer_id, prod1_id, prod2_id = create_sample_customer_and_products(client)

    create_res = client.post("/api/invoices", json={
        "customer_id": customer_id,
        "invoice_date": str(date.today()),
        "lines": [
            {"product_id": prod1_id, "quantity": 1},
            {"product_id": prod2_id, "quantity": 2}
        ]
    })
    invoice_id = create_res.json()["id"]

    # Get lines endpoint
    lines_res = client.get(f"/api/invoices/{invoice_id}/lines")
    assert lines_res.status_code == status.HTTP_200_OK
    lines_data = lines_res.json()
    assert len(lines_data) == 2

    # Delete invoice
    del_res = client.delete(f"/api/invoices/{invoice_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify deleted
    assert client.get(f"/api/invoices/{invoice_id}").status_code == status.HTTP_404_NOT_FOUND
