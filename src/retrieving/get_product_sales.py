from . import connect
from ... import CassandraRepository

def get_product_sales(
        table_name,
        product_id, 
        columns,
        start_date,
        end_date,
        repo = CassandraRepository(),
        ):
    if not start_date and not end_date:
        repo.get_sales_records(
            table_name,
            product_id,
            columns,
        )
    if not end_date:
        repo.get_sales_records(
            table_name,
            product_id,
            columns,
            start_date
        )
    if not start_date:
        repo.get_sales_records(
            table_name,
            product_id,
            columns,
            start_date
        )
        