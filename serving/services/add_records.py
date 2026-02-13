from repo.cassandra_repo import CassandraRepository

def add_sales_record(
        record: dict,
        table_name: str = "Sales",
        repo = None
    ):
    if repo is None:
        repo = CassandraRepository()
    """
    Adds a sales record to the database.
    
    Args:
        record: The sales record to add.
        table_name: The name of the sales table.
        repo: The Cassandra repository to use for adding sales records.
    """
    repo.add_sales_record(
        table_name=table_name,
        record=record
    )