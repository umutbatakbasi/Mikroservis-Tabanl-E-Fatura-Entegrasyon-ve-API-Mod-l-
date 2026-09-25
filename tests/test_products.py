from decimal import Decimal
from fastapi import status


def test_create_product(client):
    """Scenario 3: Product oluşturma."""
    payload = {
        "code": "PRD-TEST-1",
        "name": "Test Ürün",
        "description": "Açıklama",
        "unit_price": 250.00,
        "vat_rate": 20.00
    }
    response = client.post("/api/products", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] is not None
    assert data["code"] == payload["code"]
    assert Decimal(str(data["unit_price"])) == Decimal("250.00")
    assert Decimal(str(data["vat_rate"])) == Decimal("20.00")


def test_list_products(client):
    """Scenario 4: Product listeleme."""
    client.post("/api/products", json={"code": "PRD-L1", "name": "Ürün 1", "unit_price": 100, "vat_rate": 10})
    client.post("/api/products", json={"code": "PRD-L2", "name": "Ürün 2", "unit_price": 200, "vat_rate": 20})

    response = client.get("/api/products")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_duplicate_product_code_conflict(client):
    """Scenario 10: Duplicate product code kontrolü."""
    payload = {
        "code": "PRD-UNIQUE-1",
        "name": "Ürün Orijinal",
        "unit_price": 500,
        "vat_rate": 20
    }
    res1 = client.post("/api/products", json=payload)
    assert res1.status_code == status.HTTP_201_CREATED

    res2 = client.post("/api/products", json={
        "code": "PRD-UNIQUE-1",
        "name": "Çift Kodlu Ürün",
        "unit_price": 600,
        "vat_rate": 20
    })
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in res2.json()["detail"]


def test_product_validation():
    """Verify validation on negative unit_price and out-of-range vat_rate."""
    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        # Negative unit price
        res_price = client.post("/api/products", json={
            "code": "PRD-BAD-1",
            "name": "Hatalı Fiyat",
            "unit_price": -10.0,
            "vat_rate": 20.0
        })
        assert res_price.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # VAT rate > 100
        res_vat = client.post("/api/products", json={
            "code": "PRD-BAD-2",
            "name": "Hatalı KDV",
            "unit_price": 100.0,
            "vat_rate": 120.0
        })
        assert res_vat.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_product_by_id(client):
    """Test get product by ID and 404."""
    create_res = client.post("/api/products", json={
        "code": "PRD-GET-1",
        "name": "Detay Ürün",
        "unit_price": 150,
        "vat_rate": 20
    })
    product_id = create_res.json()["id"]

    get_res = client.get(f"/api/products/{product_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["code"] == "PRD-GET-1"

    not_found = client.get("/api/products/88888")
    assert not_found.status_code == status.HTTP_404_NOT_FOUND


def test_update_and_delete_product(client):
    """Test update and delete product."""
    create_res = client.post("/api/products", json={
        "code": "PRD-UPD-1",
        "name": "Eski Ürün",
        "unit_price": 300,
        "vat_rate": 10
    })
    product_id = create_res.json()["id"]

    # Update
    update_res = client.put(f"/api/products/{product_id}", json={
        "name": "Güncel Ürün",
        "unit_price": 350.00
    })
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["name"] == "Güncel Ürün"
    assert Decimal(str(update_res.json()["unit_price"])) == Decimal("350.00")

    # Delete
    del_res = client.delete(f"/api/products/{product_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify deleted
    assert client.get(f"/api/products/{product_id}").status_code == status.HTTP_404_NOT_FOUND
