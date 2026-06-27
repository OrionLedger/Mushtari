from repo.current import get_active_repository

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
    if repo is None:
        repo = get_active_repository()
    
    if table_name is None:
        table_name = "sales"

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