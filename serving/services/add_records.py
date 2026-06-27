from repo import get_repository

def add_sales_record(
        record: dict,
        table_name: str = "sales",
        repo = None
    ):
    """
    Adds a sales record to the database using the configured repository.
    """
    if repo is None:
        repo = get_repository("postgres", shared=True)

    return repo.add_record(
        table_name=table_name,
        record=record
    )