from repo import get_repository
from etl.config.settings import get_settings

def get_product_sales(
        product_id, 
        columns,
        start_date = None,
        end_date = None,
        table_name=None,
        repo = None,
        ):
    """
    Retrieves sales records for a specific product within a given date range.
    Uses the repository factory to support multiple storage backends.
    """
    settings = get_settings()
    
    if repo is None:
        c_settings = settings.extract.cassandra
        repo = get_repository(
            "cassandra",
            username=c_settings.username,
            password=c_settings.password,
            contact_points=c_settings.contact_points,
            port=c_settings.port
        )
        if c_settings.keyspace:
            repo.set_keyspace(c_settings.keyspace)
    
    if table_name is None:
        table_name = settings.extract.cassandra.default_table

    filters = {"product_id": product_id}
    if start_date:
        filters["sell_date__gte"] = start_date
    if end_date:
        filters["sell_date__lte"] = end_date
        
    return repo.get_record(
        table_name=table_name,
        filters=filters,
        columns=columns
    )