from .. import Mongo_DB_Module

class DBRepo:
    def __init__(self, db_module = Mongo_DB_Module()):
        self.db_module = db_module

    def add_data(self, collection_name, data):
        self.db_module.add_record(collection_name, data)

    def fetch_data(self, collection_name, query):
        return self.db_module.get_record(collection_name, query)

    def update_data(self, collection_name, query, update_values):
        self.db_module.update_record(collection_name, query, update_values)

    def delete_data(self, collection_name, query):
        self.db_module.delete_record(collection_name, query)