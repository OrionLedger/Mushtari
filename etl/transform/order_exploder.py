"""
etl/transform/order_exploder.py

Transforms raw order records into granular demand events (fact_sales).
Supports dynamic mapping and JSON unnesting.
"""

from typing import Any, Dict, List, Tuple
import pandas as pd
import json
from prefect import task
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

@task(name="explode-orders")
def explode_orders(
    df: pd.DataFrame,
    column_mapping: Dict[str, str],
    source_id: int,
    items_source_type: str = "json_column"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Explodes order records into individual line items.
    
    Returns:
        (df_backlog, df_sales, df_customers)
    """
    if df.empty:
        return df, pd.DataFrame(), pd.DataFrame()

    logger.info(f"Exploding {len(df)} orders from source {source_id}...")

    # 1. Map columns to internal names
    # Mapping is {internal_name: source_name}
    internal_to_source = column_mapping
    source_to_internal = {v: k for k, v in column_mapping.items()}
    
    # Check if required internal fields are mapped
    required_mapped = ["order_id", "order_date"]
    for req in required_mapped:
        if req not in internal_to_source:
             logger.warning(f"Required field '{req}' is not mapped. Extraction might fail.")

    # Apply mapping to a copy
    df_mapped = df.copy()
    df_mapped = df_mapped.rename(columns=source_to_internal)

    # 2. Extract Backlog (Orders)
    # We keep the raw items as a JSON string for the backlog
    backlog_cols = ["order_id", "customer_id", "order_date", "status", "total_amount"]
    # Add any missing cols as None
    for col in backlog_cols:
        if col not in df_mapped.columns:
            df_mapped[col] = None

    df_backlog = df_mapped[backlog_cols].copy()
    df_backlog["source_id"] = source_id
    
    # Store items_column as raw_items in backlog
    items_col = internal_to_source.get("items_column", "items")
    if items_col in df.columns:
        df_backlog["raw_items"] = df[items_col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)
    else:
        df_backlog["raw_items"] = None

    # 3. Explode Sales Items
    all_items = []
    
    for idx, row in df_mapped.iterrows():
        order_items = []
        raw_row = df.iloc[idx]
        
        # Determine items source
        if items_source_type == "json_column":
            items_raw = raw_row.get(items_col)
            if isinstance(items_raw, str):
                try:
                    order_items = json.loads(items_raw)
                except:
                    order_items = []
            elif isinstance(items_raw, list):
                order_items = items_raw
        else:
            # Separate table mode - handled in extractor usually, 
            # but if it's already joined/flat in df, we treat it as 1-item per row or similar
            # For now, assume if not json_column, it's already exploded or items are in a list
            pass

        if not isinstance(order_items, list):
            order_items = []

        for item in order_items:
            # Map item fields
            # Item fields: product_id, quantity, unit_price, discount
            p_id = item.get(internal_to_source.get("product_id", "product_id"))
            qty = item.get(internal_to_source.get("quantity", "quantity"), 0)
            price = item.get(internal_to_source.get("unit_price", "unit_price"), 0)
            disc = item.get(internal_to_source.get("discount", "discount"), 0)
            
            try:
                qty = float(qty)
                price = float(price)
                disc = float(disc)
            except:
                qty, price, disc = 0, 0, 0

            gross = qty * price
            net = gross - disc
            
            all_items.append({
                "order_id": row["order_id"],
                "source_id": source_id,
                "product_id": str(p_id),
                "quantity": qty,
                "unit_price": price,
                "discount": disc,
                "gross_sale": gross,
                "net_sale": net,
                "sale_date": row["order_date"]
            })

    df_sales = pd.DataFrame(all_items)

    # 4. Extract Customers
    cust_cols = ["customer_id", "customer_name", "customer_email", "customer_segment", "customer_region"]
    for col in cust_cols:
        if col not in df_mapped.columns:
            df_mapped[col] = None
            
    df_customers = df_mapped[cust_cols].dropna(subset=["customer_id"]).drop_duplicates(subset=["customer_id"])
    df_customers = df_customers.rename(columns={
        "customer_name": "name",
        "customer_email": "email",
        "customer_segment": "segment",
        "customer_region": "region"
    })
    
    logger.info(f"Explosion complete: {len(df_backlog)} orders -> {len(df_sales)} sales events.")
    return df_backlog, df_sales, df_customers
