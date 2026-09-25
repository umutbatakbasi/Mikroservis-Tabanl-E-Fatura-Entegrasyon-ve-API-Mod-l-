from fastapi import status


def test_create_customer(client):
    """Scenario 1: Customer oluşturma."""
    payload = {
        "tax_number": "1234567890",
        "name": "Test Müşteri Ltd.",
        "email": "test@musteri.com",
        "phone": "+90 555 111 2233",
        "address": "İstanbul / Türkiye"
    }
    response = client.post("/api/customers", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] is not None
    assert data["tax_number"] == payload["tax_number"]
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]


def test_list_customers(client):
    """Scenario 2: Customer listeleme."""
    # Create two customers
    client.post("/api/customers", json={"tax_number": "1111111111", "name": "Müşteri 1"})
    client.post("/api/customers", json={"tax_number": "2222222222", "name": "Müşteri 2"})

    response = client.get("/api/customers")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_duplicate_tax_number_conflict(client):
    """Scenario 9: Duplicate tax_number kontrolü."""
    payload = {
        "tax_number": "1234567890",
        "name": "Müşteri A",
        "email": "a@test.com"
    }
    # First creation should succeed
    res1 = client.post("/api/customers", json=payload)
    assert res1.status_code == status.HTTP_201_CREATED

    # Second creation with identical tax_number should fail with 409 CONFLICT
    res2 = client.post("/api/customers", json={
        "tax_number": "1234567890",
        "name": "Müşteri B",
        "email": "b@test.com"
    })
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in res2.json()["detail"]


def test_get_customer_by_id(client):
    """Test get customer by ID (success and 404)."""
    create_res = client.post("/api/customers", json={
        "tax_number": "3333333333",
        "name": "Bulunacak Müşteri"
    })
    customer_id = create_res.json()["id"]

    # Success
    get_res = client.get(f"/api/customers/{customer_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["name"] == "Bulunacak Müşteri"

    # Not found
    not_found_res = client.get("/api/customers/99999")
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND


def test_update_customer(client):
    """Test updating customer data and tax_number uniqueness validation."""
    create_res = client.post("/api/customers", json={
        "tax_number": "4444444444",
        "name": "Eski İsim",
        "email": "eski@test.com"
    })
    customer_id = create_res.json()["id"]

    update_payload = {
        "name": "Yeni İsim",
        "email": "yeni@test.com"
    }
    update_res = client.put(f"/api/customers/{customer_id}", json=update_payload)
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["name"] == "Yeni İsim"
    assert update_res.json()["email"] == "yeni@test.com"


def test_delete_customer(client):
    """Test deleting customer."""
    create_res = client.post("/api/customers", json={
        "tax_number": "5555555555",
        "name": "Silinecek Müşteri"
    })
    customer_id = create_res.json()["id"]

    del_res = client.delete(f"/api/customers/{customer_id}")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify deleted
    get_res = client.get(f"/api/customers/{customer_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND
