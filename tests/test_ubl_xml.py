from datetime import date
from decimal import Decimal
import xml.etree.ElementTree as ET
from fastapi import status
from app.services.ubl_service import ubl_service, UBLTRService


def create_sample_customer_and_products(client):
    """Helper fixture setup for creating a customer and two products."""
    cust_res = client.post("/api/customers", json={
        "tax_number": "1234567890",
        "name": "Bilişim Çözümleri A.Ş.",
        "email": "bilgi@bilisim.com",
        "phone": "+90 212 999 8877",
        "address": "İstanbul / Türkiye"
    })
    customer_id = cust_res.json()["id"]

    prod1_res = client.post("/api/products", json={
        "code": "SRV-UBL-1",
        "name": "Bulut Lisans Paketi",
        "unit_price": 5000.00,
        "vat_rate": 20.00
    })
    prod1_id = prod1_res.json()["id"]

    return customer_id, prod1_id


def test_vkn_tckn_validation():
    """Verify validation logic for Turkish VKN (10 digits) and TCKN (11 digits)."""
    assert UBLTRService.validate_vkn_tckn("1234567890") is True   # VKN (10)
    assert UBLTRService.validate_vkn_tckn("12345678901") is True  # TCKN (11)
    assert UBLTRService.validate_vkn_tckn("12345") is False        # Too short
    assert UBLTRService.validate_vkn_tckn("123456789012") is False # Too long
    assert UBLTRService.validate_vkn_tckn("ABCDEFGHIJ") is False   # Letters
    assert UBLTRService.validate_vkn_tckn("") is False             # Empty


def test_get_invoice_xml_endpoint_application_xml(client):
    """
    Day 10: Test GET /invoices/{id}/xml returns HTTP 200 with 'application/xml'
    Content-Type and valid GİB UBL-TR 1.2 XML tree.
    """
    customer_id, prod1_id = create_sample_customer_and_products(client)

    # 1. Create an invoice
    create_res = client.post("/api/invoices", json={
        "customer_id": customer_id,
        "invoice_date": str(date.today()),
        "lines": [{"product_id": prod1_id, "quantity": 2}]
    })
    assert create_res.status_code == status.HTTP_201_CREATED
    invoice_id = create_res.json()["id"]
    invoice_number = create_res.json()["invoice_number"]

    # 2. Request XML via GET /api/invoices/{id}/xml
    xml_res = client.get(f"/api/invoices/{invoice_id}/xml")
    assert xml_res.status_code == status.HTTP_200_OK
    assert "application/xml" in xml_res.headers.get("content-type", "")

    # 3. Parse XML content and verify UBL-TR tags
    xml_text = xml_res.text
    root = ET.fromstring(xml_text)

    # Root tag check (namespaced)
    assert root.tag == "{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice"

    # Search for mandatory UBL-TR elements
    ns = {
        "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    }

    inv_id_elem = root.find("cbc:ID", ns)
    assert inv_id_elem is not None
    assert inv_id_elem.text == invoice_number

    supplier_elem = root.find("cac:AccountingSupplierParty", ns)
    assert supplier_elem is not None

    customer_elem = root.find("cac:AccountingCustomerParty", ns)
    assert customer_elem is not None

    tax_total_elem = root.find("cac:TaxTotal", ns)
    assert tax_total_elem is not None

    line_elems = root.findall("cac:InvoiceLine", ns)
    assert len(line_elems) == 1


def test_get_invoice_xml_direct_route(client):
    """Day 10: Test direct /invoices/{id}/xml route without /api prefix."""
    customer_id, prod1_id = create_sample_customer_and_products(client)

    create_res = client.post("/invoices", json={
        "customer_id": customer_id,
        "invoice_date": str(date.today()),
        "lines": [{"product_id": prod1_id, "quantity": 1}]
    })
    invoice_id = create_res.json()["id"]

    xml_res = client.get(f"/invoices/{invoice_id}/xml")
    assert xml_res.status_code == status.HTTP_200_OK
    assert "application/xml" in xml_res.headers.get("content-type", "")


def test_get_invoice_xml_not_found_404(client):
    """Day 10: Non-existent invoice returns 404."""
    xml_res = client.get("/api/invoices/99999/xml")
    assert xml_res.status_code == status.HTTP_404_NOT_FOUND
