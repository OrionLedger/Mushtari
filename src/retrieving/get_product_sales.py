from repo.cassandra_repo import CassandraRepository

def get_product_sales(
        product_id, 
        columns,
        start_date,
        end_date,
        table_name='sales',
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
        