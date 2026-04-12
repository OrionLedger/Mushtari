import pandera as pa
from pandera import Column, Check, DataFrameSchema
import pandas as pd

# Core Sales constraints
sales_schema = DataFrameSchema({
    "product_id": Column(pa.Int, Check.greater_than_or_equal_to(0), coerce=True, nullable=True),
    # Sales must not be historically negative unless dealing with refunds, but typically we require >= 0
    "sales": Column(float, Check.greater_than_or_equal_to(0.0), coerce=True, required=False, nullable=True),
    "quantity": Column(float, Check.greater_than_or_equal_to(0.0), coerce=True, required=False, nullable=True),
    "price": Column(float, Check.greater_than_or_equal_to(0.0), coerce=True, required=False, nullable=True),
    # sell_date shouldn't be parsed if missing or corrupted completely.
    "sell_date": Column(pa.DateTime, required=False, nullable=True, coerce=True),
    "date": Column(pa.DateTime, required=False, nullable=True, coerce=True)
}, strict=False) # strict=False allows other unknown columns to exist without failing

def get_schema(name: str) -> DataFrameSchema:
    schemas = {
        "sales": sales_schema,
    }
    return schemas.get(name.lower(), sales_schema)
