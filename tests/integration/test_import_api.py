"""
Integration tests for the Excel Import API endpoints.

Tests file upload, validation, and response format.
Uses FastAPI TestClient against the real app.
"""

import os
import tempfile
import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ─── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def valid_products_excel():
    """Create a valid products Excel file in memory."""
    df = pd.DataFrame({
        "sku_code": ["SKU-INT-001", "SKU-INT-002"],
        "name": ["Integration Product A", "Integration Product B"],
        "base_price": [15.99, 25.99],
        "unit_cost": [8.00, 13.00],
        "current_stock": [200, 150],
        "safety_stock": [30, 20],
        "status": ["active", "active"],
        "category_name": ["Integration Test Cat", "Integration Test Cat"],
    })
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return buffer


@pytest.fixture
def valid_orders_excel():
    """Create a valid orders Excel file in memory.
    Uses SKU codes that may not exist in the database.
    """
    df = pd.DataFrame({
        "order_id": ["ORD-INT-001", "ORD-INT-002"],
        "order_date": ["2026-06-10", "2026-06-11"],
        "customer_name": ["Integration Customer", "Another Customer"],
        "customer_email": ["int@test.com", "another@test.com"],
        "product_sku": ["SKU-INT-001", "SKU-INT-002"],
        "quantity": [8, 12],
        "price_at_sale": [15.99, 25.99],
        "status": ["completed", "completed"],
    })
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return buffer


@pytest.fixture
def invalid_format_file():
    """Create a non-Excel file."""
    return io.BytesIO(b"This is not an Excel file")


@pytest.fixture
def missing_columns_excel():
    """Create an Excel file missing required columns."""
    df = pd.DataFrame({
        "some_column": [1, 2],
        "other_column": ["A", "B"],
    })
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return buffer


# ─── Tests: POST /api/import/products ────────────────────────────────────

def test_import_products_endpoint_accepts_file(valid_products_excel):
    """A valid products Excel file should be accepted and return 200."""
    response = client.post(
        "/api/import/products",
        files={"file": ("products.xlsx", valid_products_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("completed", "error")
    assert "total_rows" in data
    assert "rows_imported" in data
    assert "rows_failed" in data


def test_import_products_rejects_non_excel(invalid_format_file):
    """A non-Excel file should be rejected with 400."""
    response = client.post(
        "/api/import/products",
        files={"file": ("test.txt", invalid_format_file, "text/plain")},
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_import_products_missing_columns(missing_columns_excel):
    """An Excel file missing required columns should return 200 with error status."""
    response = client.post(
        "/api/import/products",
        files={"file": ("bad_products.xlsx", missing_columns_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "sku_code" in data["message"]


def test_import_products_no_file():
    """Request without a file should return 422."""
    response = client.post("/api/import/products")
    assert response.status_code == 422


# ─── Tests: POST /api/import/orders ──────────────────────────────────────

def test_import_orders_endpoint_accepts_file(valid_orders_excel):
    """A valid orders Excel file should be accepted."""
    response = client.post(
        "/api/import/orders",
        files={"file": ("orders.xlsx", valid_orders_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("completed", "error")
    assert "total_rows" in data


def test_import_orders_rejects_non_excel(invalid_format_file):
    """A non-Excel file should be rejected with 400."""
    response = client.post(
        "/api/import/orders",
        files={"file": ("test.txt", invalid_format_file, "text/plain")},
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_import_orders_missing_columns(missing_columns_excel):
    """An Excel file missing required columns should return error."""
    response = client.post(
        "/api/import/orders",
        files={"file": ("bad_orders.xlsx", missing_columns_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    # Should contain at least "order_id" in the message
    assert "order_id" in data["message"]


# ─── Tests: GET /api/import/templates ────────────────────────────────────

def test_get_products_template_info():
    """Products template endpoint should return metadata."""
    response = client.get("/api/import/template/products")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "expected_columns" in data
    assert "required" in data["expected_columns"]
    assert "sku_code" in data["expected_columns"]["required"]


def test_get_orders_template_info():
    """Orders template endpoint should return metadata."""
    response = client.get("/api/import/template/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "expected_columns" in data
    assert "order_id" in data["expected_columns"]["required"]


def test_download_products_template_file():
    """Download the actual products template .xlsx file."""
    response = client.get("/api/import/template/products/file")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "products_template" in response.headers.get("content-disposition", "")


def test_download_orders_template_file():
    """Download the actual orders template .xlsx file."""
    response = client.get("/api/import/template/orders/file")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "orders_template" in response.headers.get("content-disposition", "")
