import pandera as pa
from pandera import Column, Check, DataFrameSchema
import pandas as pd

# Core Sales constraints
sales_schema = DataFrameSchema({
    "product_id": Column(pa.Int, Check.greater_than_or_equal_to(0), coerce=True, nullable=True),
    "sales": Column(float, Check.greater_than_or_equal_to(0.0), coerce=True, required=False, nullable=True),
    "quantity": Column(float, Check.greater_than_or_equal_to(0.0), coerce=True, required=False, nullable=True),
    "price": Column(float, Check.greater_than_or_equal_to(0.0), coerce=True, required=False, nullable=True),
    "sell_date": Column(pa.DateTime, required=False, nullable=True, coerce=True),
    "date": Column(pa.DateTime, required=False, nullable=True, coerce=True)
}, strict=False)

# Order records constraints
order_schema = DataFrameSchema({
    "order_id": Column(pa.String, required=True),
    "order_date": Column(pa.DateTime, required=True, coerce=True),
    "customer_id": Column(pa.String, nullable=True),
}, strict=False)

# Exploded order items constraints
order_items_schema = DataFrameSchema({
    "order_id": Column(pa.String, required=True),
    "product_id": Column(pa.String, required=True),
    "quantity": Column(float, Check.greater_than_or_equal_to(0.0), coerce=True),
    "unit_price": Column(float, Check.greater_than_or_equal_to(0.0), coerce=True),
    "gross_sale": Column(float, coerce=True),
    "sale_date": Column(pa.DateTime, coerce=True)
}, strict=False)

def get_schema(name: str) -> DataFrameSchema:
    schemas = {
        "sales": sales_schema,
        "orders": order_schema,
        "order_items": order_items_schema,
    }
    return schemas.get(name.lower(), sales_schema)
