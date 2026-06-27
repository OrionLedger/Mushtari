from repo.current import get_active_repository

def add_sales_record(
        record: dict,
        table_name: str = "sales",
        repo = None
    ):
    """
    Adds a sales record to the database using the configured repository.
    """
    if repo is None:
        repo = get_active_repository()

    return repo.add_record(
        table_name=table_name,
        record=record
    )