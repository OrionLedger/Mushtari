"""
serving/services/excel_importer.py

Excel import service for Products and Orders/Sales data.
Parses .xlsx files, validates, maps columns, and inserts into PostgreSQL
using the existing repository layer.
"""

import uuid
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

from repo import get_repository
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


# ─── Expected Columns ──────────────────────────────────────────────────────

PRODUCTS_EXPECTED_COLUMNS = {
    "required": ["sku_code", "name"],
    "optional": [
        "base_price", "unit_cost", "current_stock", "safety_stock",
        "status", "category_name", "weight", "dimensions",
    ],
}

ORDERS_EXPECTED_COLUMNS = {
    "required": ["order_id", "order_date", "product_sku", "quantity", "price_at_sale"],
    "optional": [
        "customer_name", "customer_email", "status", "total_amount",
    ],
}


# ─── Import: Products ──────────────────────────────────────────────────────

def import_products_from_excel(file_path: str) -> Dict[str, Any]:
    """
    Import product data from an Excel file into the products table.

    Expected columns: sku_code, name, [base_price, unit_cost, current_stock,
                      safety_stock, status, category_name, weight, dimensions]

    Args:
        file_path: Path to the .xlsx file.

    Returns:
        Dict with import summary: status, rows_imported, rows_failed, errors, warnings.
    """
    repo = get_repository("postgres", shared=True)
    result = _init_result()

    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception as e:
        return {"status": "error", "message": f"Failed to read Excel file: {e}"}

    # Normalise column names
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    # Validate required columns
    missing = _validate_columns(df, PRODUCTS_EXPECTED_COLUMNS)
    if missing:
        return {"status": "error", "message": f"Missing required columns: {', '.join(missing)}"}

    total_rows = len(df)
    result["total_rows"] = total_rows

    for idx, row in df.iterrows():
        row_num = idx + 2  # +1 for header, +1 for 0-index
        try:
            sku_raw = row.get("sku_code")
            name_raw = row.get("name")
            sku = str(sku_raw).strip() if not _is_empty(sku_raw) else ""
            name = str(name_raw).strip() if not _is_empty(name_raw) else ""

            if not sku or not name:
                result["warnings"].append(f"Row {row_num}: skipped — sku_code and name are required")
                result["rows_skipped"] += 1
                continue

            # Build product record
            product = {
                "sku_code": sku,
                "name": name,
            }

            # Parse numeric fields
            for field in ["base_price", "unit_cost", "weight"]:
                val = row.get(field)
                if val is not None and not _is_empty(val):
                    try:
                        product[field] = float(val)
                    except (ValueError, TypeError):
                        result["warnings"].append(f"Row {row_num}: invalid {field} '{val}', using 0")

            for field in ["current_stock", "safety_stock"]:
                val = row.get(field)
                if val is not None and not _is_empty(val):
                    try:
                        product[field] = int(float(val))
                    except (ValueError, TypeError):
                        result["warnings"].append(f"Row {row_num}: invalid {field} '{val}', using 0")

            # Dimensions
            dims = row.get("dimensions")
            if dims is not None and not _is_empty(dims):
                product["dimensions"] = str(dims).strip()

            # Status (validate against CHECK constraint)
            status = row.get("status")
            if status is not None and not _is_empty(status):
                s = str(status).strip().lower()
                if s in ("active", "retired", "draft"):
                    product["status"] = s
                else:
                    result["warnings"].append(f"Row {row_num}: invalid status '{s}', using 'active'")

            # Category lookup/create
            cat_name = row.get("category_name")
            if cat_name is not None and not _is_empty(cat_name):
                cat_id = _find_or_create_category(str(cat_name).strip(), repo)
                if cat_id is not None:
                    product["category_id"] = cat_id

            # Check for existing product by sku_code
            existing = repo.get_record("products", filters={"sku_code": sku})
            if existing:
                # Update existing
                pid = existing[0]["id"]
                # Remove sku_code from updates since it's the key
                updates = {k: v for k, v in product.items() if k != "sku_code"}
                ok = repo.update_record("products", pid, updates, id_column="id")
                if ok:
                    result["rows_updated"] += 1
                else:
                    result["rows_failed"] += 1
                    result["errors"].append(f"Row {row_num}: failed to update product '{sku}'")
            else:
                # Insert new
                ok = repo.add_record("products", product)
                if ok:
                    result["rows_imported"] += 1
                else:
                    result["rows_failed"] += 1
                    result["errors"].append(f"Row {row_num}: failed to insert product '{sku}'")

        except Exception as e:
            result["rows_failed"] += 1
            result["errors"].append(f"Row {row_num}: unexpected error — {e}")

    result["status"] = "completed"
    _cleanup(result)
    logger.info(f"Products import completed: {result['rows_imported']} imported, "
                f"{result['rows_updated']} updated, {result['rows_failed']} failed")
    return result


# ─── Import: Orders ────────────────────────────────────────────────────────

def import_orders_from_excel(file_path: str) -> Dict[str, Any]:
    """
    Import order/sales data from an Excel file.

    Expected columns per row (flat line-item format):
      order_id, order_date, product_sku, quantity, price_at_sale,
      [customer_name, customer_email, status, total_amount]

    Each unique order_id creates one order record.
    Each row creates one sales (line-item) record.

    Args:
        file_path: Path to the .xlsx file.

    Returns:
        Dict with import summary.
    """
    repo = get_repository("postgres", shared=True)
    result = _init_result()

    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception as e:
        return {"status": "error", "message": f"Failed to read Excel file: {e}"}

    # Normalise column names
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    # Validate required columns
    missing = _validate_columns(df, ORDERS_EXPECTED_COLUMNS)
    if missing:
        return {"status": "error", "message": f"Missing required columns: {', '.join(missing)}"}

    total_rows = len(df)
    result["total_rows"] = total_rows

    # Track created orders to avoid duplicates
    created_orders: Dict[str, str] = {}  # order_id → UUID
    created_customers: Dict[str, str] = {}  # customer_name → UUID

    for idx, row in df.iterrows():
        row_num = idx + 2
        try:
            oid_raw = row.get("order_id")
            order_id_str = str(oid_raw).strip() if not _is_empty(oid_raw) else ""
            if not order_id_str:
                result["warnings"].append(f"Row {row_num}: skipped — order_id is empty")
                result["rows_skipped"] += 1
                continue

            psku_raw = row.get("product_sku")
            product_sku = str(psku_raw).strip() if not _is_empty(psku_raw) else ""
            if not product_sku:
                result["warnings"].append(f"Row {row_num}: skipped — product_sku is empty")
                result["rows_skipped"] += 1
                continue

            # Parse order_date
            order_date = row.get("order_date")
            if order_date is None or _is_empty(order_date):
                result["warnings"].append(f"Row {row_num}: skipped — order_date is required")
                result["rows_skipped"] += 1
                continue
            try:
                order_dt = pd.to_datetime(order_date)
                if pd.isna(order_dt):
                    raise ValueError("NaT")
            except (ValueError, TypeError):
                result["errors"].append(f"Row {row_num}: invalid order_date '{order_date}'")
                result["rows_failed"] += 1
                continue

            # Parse quantity and price
            try:
                quantity = float(row.get("quantity", 0))
            except (ValueError, TypeError):
                result["errors"].append(f"Row {row_num}: invalid quantity")
                result["rows_failed"] += 1
                continue

            try:
                price_at_sale = float(row.get("price_at_sale", 0))
            except (ValueError, TypeError):
                result["errors"].append(f"Row {row_num}: invalid price_at_sale")
                result["rows_failed"] += 1
                continue

            # Look up product by sku_code
            product_rows = repo.get_record("products", filters={"sku_code": product_sku})
            if not product_rows:
                result["errors"].append(f"Row {row_num}: product_sku '{product_sku}' not found in database")
                result["rows_failed"] += 1
                continue
            product_id = product_rows[0]["id"]

            # ── Create or get customer ──
            customer_id = None
            customer_name = row.get("customer_name")
            if customer_name is not None and not _is_empty(customer_name):
                cname = str(customer_name).strip()
                if cname in created_customers:
                    customer_id = created_customers[cname]
                else:
                    customer_email = row.get("customer_email")
                    cemail = str(customer_email).strip() if customer_email is not None and not _is_empty(customer_email) else None
                    cust_id = _find_or_create_customer(cname, cemail, repo)
                    if cust_id:
                        created_customers[cname] = cust_id
                        customer_id = cust_id
                    else:
                        result["warnings"].append(f"Row {row_num}: failed to create customer '{cname}'")

            # ── Create order if not already created ──
            order_uuid = created_orders.get(order_id_str)
            if order_uuid is None:
                order_uuid = _create_order(
                    order_id=order_id_str,
                    order_date=order_dt,
                    customer_id=customer_id,
                    status=row.get("status"),
                    total_amount=row.get("total_amount"),
                    repo=repo,
                )
                if order_uuid:
                    created_orders[order_id_str] = order_uuid
                else:
                    result["errors"].append(f"Row {row_num}: failed to create order '{order_id_str}'")
                    result["rows_failed"] += 1
                    continue

            # ── Insert sales line item ──
            sales_record = {
                "order_id": order_uuid,
                "product_id": product_id,
                "ds": order_dt,
                "quantity": quantity,
                "price_at_sale": price_at_sale,
            }
            if customer_id:
                sales_record["customer_id"] = customer_id

            ok = repo.add_record("sales", sales_record)
            if ok:
                result["rows_imported"] += 1
            else:
                result["rows_failed"] += 1
                result["errors"].append(f"Row {row_num}: failed to insert sales record")

        except Exception as e:
            result["rows_failed"] += 1
            result["errors"].append(f"Row {row_num}: unexpected error — {e}")

    result["status"] = "completed"
    _cleanup(result)
    logger.info(f"Orders import completed: {result['rows_imported']} items imported, "
                f"{result['rows_failed']} failed, {result['rows_skipped']} skipped")
    return result


# ─── Template Generator ────────────────────────────────────────────────────

def generate_products_template() -> str:
    """Generate a sample Excel template for product import."""
    df = pd.DataFrame({
        "sku_code": ["SKU001", "SKU002"],
        "name": ["Sample Product A", "Sample Product B"],
        "base_price": [29.99, 49.99],
        "unit_cost": [15.00, 25.00],
        "current_stock": [100, 50],
        "safety_stock": [20, 10],
        "status": ["active", "active"],
        "category_name": ["Electronics", "Home Goods"],
        "weight": [1.5, 2.0],
        "dimensions": ["10x5x3", "12x8x4"],
    })
    path = _save_temp_template(df, "products_template.xlsx")
    return path


def generate_orders_template() -> str:
    """Generate a sample Excel template for order import."""
    df = pd.DataFrame({
        "order_id": ["ORD-001", "ORD-001", "ORD-002"],
        "order_date": ["2026-06-01", "2026-06-01", "2026-06-02"],
        "customer_name": ["Acme Corp", "Acme Corp", "Beta Inc"],
        "customer_email": ["orders@acme.com", "orders@acme.com", "info@beta.com"],
        "product_sku": ["SKU001", "SKU002", "SKU001"],
        "quantity": [10, 5, 3],
        "price_at_sale": [29.99, 49.99, 29.99],
        "status": ["completed", "completed", "pending"],
        "total_amount": [549.85, 549.85, 89.97],
    })
    path = _save_temp_template(df, "orders_template.xlsx")
    return path


# ─── Helpers ───────────────────────────────────────────────────────────────

def _init_result() -> Dict[str, Any]:
    return {
        "status": "processing",
        "total_rows": 0,
        "rows_imported": 0,
        "rows_updated": 0,
        "rows_failed": 0,
        "rows_skipped": 0,
        "errors": [],
        "warnings": [],
        "duration_ms": 0,
    }


def _validate_columns(df: pd.DataFrame, expected: Dict[str, List[str]]) -> List[str]:
    """Check that all required columns exist in the DataFrame."""
    actual = set(str(c).lower().strip() for c in df.columns)
    missing = []
    for col in expected["required"]:
        if col.lower() not in actual:
            missing.append(col)
    return missing


def _is_empty(val) -> bool:
    """Check if a value is empty/NaN/None."""
    if val is None:
        return True
    if isinstance(val, float) and np.isnan(val):
        return True
    if isinstance(val, str) and val.strip() == "":
        return True
    return False


def _find_or_create_category(category_name: str, repo) -> Optional[int]:
    """Look up a category by name, or create it if it doesn't exist."""
    try:
        existing = repo.get_record("categories", filters={"name": category_name})
        if existing:
            return existing[0]["id"]
        repo.add_record("categories", {"name": category_name})
        created = repo.get_record("categories", filters={"name": category_name})
        if created:
            return created[0]["id"]
    except Exception as e:
        logger.warning(f"Failed to find/create category '{category_name}': {e}")
    return None


def _find_or_create_customer(name: str, email: Optional[str], repo) -> Optional[str]:
    """Look up or create a customer record. Returns customer UUID."""
    try:
        if email:
            existing = repo.get_record("customers", filters={"email": email})
            if existing:
                return existing[0]["id"]
        # Fallback to name lookup
        existing = repo.get_record("customers", filters={"name": name})
        if existing:
            return existing[0]["id"]
        # Create new
        cust_data = {"name": name}
        if email:
            cust_data["email"] = email
        import uuid as _uuid
        cust_data["id"] = str(_uuid.uuid4())
        ok = repo.add_record("customers", cust_data)
        if ok:
            # Fetch back to get the ID
            fetched = repo.get_record("customers", filters={"name": name})
            if fetched:
                return fetched[0]["id"]
    except Exception as e:
        logger.warning(f"Failed to find/create customer '{name}': {e}")
    return None


def _create_order(
    order_id: str,
    order_date: datetime,
    customer_id: Optional[str],
    status: Any,
    total_amount: Any,
    repo,
) -> Optional[str]:
    """Create an order record. Returns UUID of created order, or None."""
    try:
        order_uuid = str(uuid.uuid4())
        record = {
            "id": order_uuid,
            "order_id": order_id,
            "order_date": order_date,
            "status": str(status).strip() if status is not None and not _is_empty(status) else "pending",
        }
        if customer_id:
            record["customer_id"] = customer_id
        if total_amount is not None and not _is_empty(total_amount):
            try:
                record["total_amount"] = float(total_amount)
            except (ValueError, TypeError):
                pass
        ok = repo.add_record("orders", record)
        return order_uuid if ok else None
    except Exception as e:
        logger.warning(f"Failed to create order '{order_id}': {e}")
        return None


def _save_temp_template(df: pd.DataFrame, filename: str) -> str:
    """Save a DataFrame to a temp Excel file and return its path."""
    temp_dir = Path(tempfile.gettempdir()) / "moshtari_templates"
    temp_dir.mkdir(parents=True, exist_ok=True)
    filepath = temp_dir / filename
    df.to_excel(str(filepath), index=False, engine="openpyxl")
    return str(filepath)


def _cleanup(result: Dict[str, Any]):
    """Post-process: compute duration placeholder."""
    pass
