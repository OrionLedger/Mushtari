from repo.cassandra_repo import CassandraRepository

def get_product_sales(
        product_id, 
        columns,
        start_date,
        end_date,
        table_name='sales',
        repo = None,
        ):
    if repo is None:
        repo = CassandraRepository()
    """
    Retrieves sales records for a specific product within a given date range.
    
    Args:
        product_id: The ID of the product to retrieve sales records for.
        columns: The columns to retrieve from the sales records.
        start_date: The start date of the date range.
        end_date: The end date of the date range.
        table_name: The name of the sales table.
        repo: The Cassandra repository to use for retrieving sales records.
    
    Returns:
        A list of sales records for the specified product within the given date range.
    """
    if not start_date and not end_date:
        return repo.get_sales_records(
            table_name,
            product_id,
            columns,
        )
    if not end_date:
        return repo.get_sales_records(
            table_name,
            product_id,
            columns,
            start_date=start_date
        )
    if not start_date:
        return repo.get_sales_records(
            table_name,
            product_id,
            columns,
            end_date=end_date
        )
    return repo.get_sales_records(
        table_name,
        product_id,
        columns,
        start_date=start_date,
        end_date=end_date
    )