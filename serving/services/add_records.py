from repo.cassandra_repo import CassandraRepository

def add_sales_record(
        record: dict,
        table_name: str = "Sales",
        repo = CassandraRepository()
    ):
    repo.add_sales_record(
        table_name=table_name,
        record=record
    )