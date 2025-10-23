from infrastructure import Mongo_DB_Module

db = Mongo_DB_Module(
    uri="mongodb://127.0.0.1:27017",
    db_name="orion_ledger",
)
db.initialize_db()

# Example operations
db.add_record("test_collection", {"name": "Test Record", "value": 123})
record = db.get_record("test_collection", {"name": "Test Record"})
print(record)
db.close_connection()