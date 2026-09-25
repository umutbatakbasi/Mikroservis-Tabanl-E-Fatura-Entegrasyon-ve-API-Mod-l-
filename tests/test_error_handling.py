from fastapi import status


def test_validation_error_422_custom_handler(client):
    """Test that malformed JSON or invalid schema triggers custom 422 handler."""
    # Sending invalid data types (e.g. quantity as a string that is not a number or negative)
    bad_payload = {
        "customer_id": "not-an-integer",
        "invoice_date": "invalid-date-format",
        "lines": []  # Empty lines list violates min_length=1
    }
    response = client.post("/api/invoices", json=bad_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data
    assert data["status_code"] == 422
    assert "errors" in data
    assert len(data["errors"]) > 0


def test_customer_validation_error_422(client):
    """Test invalid customer payload triggers 422."""
    bad_customer = {
        "tax_number": "short",  # min_length is 10
        "name": "",            # min_length is 2
        "email": "not-an-email"
    }
    response = client.post("/api/customers", json=bad_customer)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["status_code"] == 422
    assert len(data["errors"]) >= 1


def test_not_found_error_404(client):
    """Test 404 Not Found response formatting."""
    response = client.get("/api/customers/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["status_code"] == 404
    assert "detail" in response.json()
