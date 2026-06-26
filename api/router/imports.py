"""
api/router/imports.py

REST endpoints for Excel data import.
Upload .xlsx files to import Products or Orders/Sales data into PostgreSQL.
"""

import os
import time
import tempfile
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool

from serving.services.excel_importer import (
    import_products_from_excel,
    import_orders_from_excel,
    generate_products_template,
    generate_orders_template,
    PRODUCTS_EXPECTED_COLUMNS,
    ORDERS_EXPECTED_COLUMNS,
)
from api.models.import_models import ImportResponse, TemplateResponse
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/import", tags=["Data Import"])

ALLOWED_EXTENSIONS = {".xlsx", ".xls"}
MAX_FILE_SIZE_MB = 50


def _validate_upload(file: UploadFile):
    """Validate file extension and size."""
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )


def _save_upload(file: UploadFile) -> str:
    """Save uploaded file to a temp location and return the path."""
    temp_dir = Path(tempfile.gettempdir()) / "moshtari_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    dest = temp_dir / f"{int(time.time())}_{file.filename}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return str(dest)


# ── Import Products ────────────────────────────────────────────────────────

@router.post("/products", response_model=ImportResponse)
async def import_products(file: UploadFile = File(...)):
    """
    Upload an Excel file to import product data.

    Expected columns:
      Required: sku_code, name
      Optional: base_price, unit_cost, current_stock, safety_stock,
                status, category_name, weight, dimensions

    Products with existing sku_code are updated; new ones are inserted.
    Category names are auto-created if they don't exist.
    """
    _validate_upload(file)
    file_path = _save_upload(file)

    start = time.perf_counter()
    try:
        result = await run_in_threadpool(import_products_from_excel, file_path)
        result["duration_ms"] = round((time.perf_counter() - start) * 1000, 1)
        return ImportResponse(**result)
    except Exception as e:
        logger.error(f"Product import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    finally:
        # Clean up temp file
        try:
            os.remove(file_path)
        except OSError:
            pass


# ── Import Orders ──────────────────────────────────────────────────────────

@router.post("/orders", response_model=ImportResponse)
async def import_orders(file: UploadFile = File(...)):
    """
    Upload an Excel file to import order/sales data.

    Expected columns per row (flat line-item format):
      Required: order_id, order_date, product_sku, quantity, price_at_sale
      Optional: customer_name, customer_email, status, total_amount

    Each unique order_id creates one order record.
    Each row creates one sales (line-item) record.
    Customers are auto-created if they don't exist.

    The 'product_sku' column must reference an existing product in the database.
    Import products first if needed.
    """
    _validate_upload(file)
    file_path = _save_upload(file)

    start = time.perf_counter()
    try:
        result = await run_in_threadpool(import_orders_from_excel, file_path)
        result["duration_ms"] = round((time.perf_counter() - start) * 1000, 1)
        return ImportResponse(**result)
    except Exception as e:
        logger.error(f"Order import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass


# ── Download Templates ─────────────────────────────────────────────────────

@router.get("/template/products", response_model=TemplateResponse)
async def download_products_template():
    """
    Download a sample Excel template for product import.
    Contains example rows showing the expected column format.
    """
    try:
        filepath = await run_in_threadpool(generate_products_template)
        filename = "products_template.xlsx"
        return TemplateResponse(
            download_url=f"/api/import/template/products/file",
            description="Excel template for importing products into the catalog",
            expected_columns=PRODUCTS_EXPECTED_COLUMNS,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template generation failed: {str(e)}")


@router.get("/template/orders", response_model=TemplateResponse)
async def download_orders_template():
    """
    Download a sample Excel template for order/sales import.
    Contains example rows showing the expected column format.
    """
    try:
        filepath = await run_in_threadpool(generate_orders_template)
        filename = "orders_template.xlsx"
        return TemplateResponse(
            download_url=f"/api/import/template/orders/file",
            description="Excel template for importing orders and sales line items",
            expected_columns=ORDERS_EXPECTED_COLUMNS,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template generation failed: {str(e)}")


@router.get("/template/products/file")
async def download_products_template_file():
    """Download the actual products template Excel file."""
    filepath = generate_products_template()
    return FileResponse(
        path=filepath,
        filename="products_template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/template/orders/file")
async def download_orders_template_file():
    """Download the actual orders template Excel file."""
    filepath = generate_orders_template()
    return FileResponse(
        path=filepath,
        filename="orders_template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
