from typing import List, Optional
from datetime import datetime
from infrastructure.configs.cassandra_db import CassandraModule
from cassandra.query import SimpleStatement

class CassandraRepository:

    def __init__(
            self,
            username=None,
            password=None,
            contact_points=['127.0.0.1'],
            port = 9042
        ):
        session = CassandraModule()
        session = session.connect(username, password, contact_points, port)
        self._session = session

    def set_keyspace(self, keyspace: str):
        self._session.set_keyspace(keyspace)

    def get_sales_records(
        self,
        table_name: str = "Sales",
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

    def add_sales_record(
        self,
        table_name: str = "Sales",
        record: dict = {}
    ):
        # Add Sales Record
        columns = ", ".join(record.keys())
        placeholders = ", ".join(["%s"] * len(record))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        values = list(record.values())
        stmt = SimpleStatement(query)
        self._session.execute(stmt, tuple(values))
        
    def close(self):
        self.cluster.shutdown()
