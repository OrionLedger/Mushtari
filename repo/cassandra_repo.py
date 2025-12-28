from typing import List, Optional
from datetime import datetime
from .. import CassandraModule
from cassandra.query import SimpleStatement
class CassandraRepository:
    """
    Cassandra repository for interacting with a keyspace.
    Supports retrieving sales records.
    """

    def __init__(self):
        session = CassandraModule()
        session = session.connect()
        self._session = session

    def set_keyspace(self, keyspace: str):
        self._session.set_keyspace(keyspace)

    def get_sales_records(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        product_id: str = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        # Retrieve Sales Records
        columns = columns or ["sell_id", "product_id", "customer_id", "quantity", "price", "sell_date"]
        for col in columns:
            self._validate_identifier(col)

        columns_cql = ", ".join(columns)

        # Build query dynamically (values are %s placeholders)
        query = f"SELECT {columns_cql} FROM {table_name} WHERE product_id = %s"
        values = [product_id]

        if start_date and end_date:
            query += " AND sell_date >= %s AND sell_date <= %s"
            values.extend([start_date, end_date])
        elif start_date:
            query += " AND sell_date >= %s"
            values.append(start_date)
        elif end_date:
            query += " AND sell_date <= %s"
            values.append(end_date)

        stmt = SimpleStatement(query)
        rows = self.session.execute(stmt, tuple(values))
        return list(rows)

    def close(self):
        self.cluster.shutdown()
