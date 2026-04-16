from repo import get_repository
from etl.config.settings import get_settings

def add_sales_record(
        record: dict,
        table_name: str = None,
        repo = None
    ):
    """
    Adds a sales record to the database using the configured repository.
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

    return repo.add_record(
        table_name=table_name,
        record=record
    )