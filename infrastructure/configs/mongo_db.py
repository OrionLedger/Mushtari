from pymongo import MongoClient
from infrastructure.logging.logger import get_logger

logger = get_logger(__name__) #Set up logging for the module

class MongoDBModule:
    def __init__(self, uri, db_name):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None

    def initialize_db(self):
        """
        Initializes the database connection.
        
        Args:
            uri: The URI for the database connection.
            db_name: The name of the database to connect to.
        
        Returns:
            The database connection.
        """
        try:
            logger.info(f"Initializing database '{self.db_name}' at '{self.uri}'")
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            logger.success("Database initialized successfully.")

        except Exception as e:
            logger.exception(f"Failed to initialize database: {e}")
    
    def add_record(self, collection_name, record):
        """
        Adds a record to the specified collection.
        
        Args:
            collection_name: The name of the collection to add the record to.
            record: The record to add to the collection.
        
        Returns:
            The added record.
        """
        try:
            collection = self.db[collection_name]
            result = collection.insert_one(record)
            logger.info(f"Record added to '{collection_name}' with id: {result.inserted_id}")
        except Exception as e:
            logger.exception(f"Failed to add record to '{collection_name}': {e}")
    
    def get_record(self, collection_name, query):
        """
        Retrieves a record from the specified collection.
        
        Args:
            collection_name: The name of the collection to retrieve the record from.
            query: The query to use for retrieving the record.
        
        Returns:
            The retrieved record.
        """
        try:
            collection = self.db[collection_name]
            record = collection.find_one(query)
            logger.info(f"Record retrieved from '{collection_name}': {record}")
            return record
        except Exception as e:
            logger.exception(f"Failed to retrieve record from '{collection_name}': {e}")

    def update_record(self, collection_name, query, update_values):
        """
        Updates a record in the specified collection.
        
        Args:
            collection_name: The name of the collection to update the record in.
            query: The query to use for updating the record.
            update_values: The values to update the record with.
        
        Returns:
            The updated record.
        """
        try:
            collection = self.db[collection_name]
            result = collection.update_one(query, {'$set': update_values})
            logger.info(f"Record updated in '{collection_name}': matched {result.matched_count}, modified {result.modified_count}")
        except Exception as e:
            logger.exception(f"Failed to update record in '{collection_name}': {e}")

    def delete_record(self, collection_name, query):
        """
        Deletes a record from the specified collection.
        
        Args:
            collection_name: The name of the collection to delete the record from.
            query: The query to use for deleting the record.
        
        Returns:
            The deleted record.
        """
        try:
            collection = self.db[collection_name]
            result = collection.delete_one(query)
            logger.info(f"Record deleted from '{collection_name}': deleted {result.deleted_count}")
        except Exception as e:
            logger.exception(f"Failed to delete record from '{collection_name}': {e}")

    def close_connection(self):
        """
        Closes the database connection.
        """
        if self.client:
            self.client.close()
            logger.info("Database connection closed.")