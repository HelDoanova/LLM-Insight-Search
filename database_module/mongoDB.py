
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
import logging
from dotenv import load_dotenv
from rich.console import Console

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("search_log.log", mode='a', encoding='utf-8'), 
    ]
)

logger = logging.getLogger(__name__)
console = Console()

class MongoDB:

    def __init__(self, database_name="default_db", collection_name="default_collection"):
        load_dotenv()
        self.MONGO_DB_URI = os.getenv("MONGO_DB_URI")
        if not self.MONGO_DB_URI:
            logger.error("MONGO_DB_URI nnot found")
            raise ValueError("MongoDB URI not set") 

        try:
            # Connecting to the database
            self.client = MongoClient(self.MONGO_DB_URI, server_api=ServerApi('1')) # specifies the MongoDB Server API version - Compatibility ensured
            self.database = self.client[database_name]
            self.collection = self.database[collection_name]
            logger.info(f"Connected to MongoDB database: {database_name}, collection: {collection_name}")
        except Exception as e:
            logger.error(f"Unexpected error during MongoDB initialization: {e}")
            raise


    def save_document(self, document):
        """
        Saves a single document to the collection.

        :param document: A dictionary representing the document to be saved.
        """
        try:
            self.collection.insert_one(document)
            logger.info("Document saved successfully.")
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            raise



    def show_database(self):
        """
        Displays all databases and their collections in the MongoDB instance.
        """
        try:
            for db_name in self.client.list_database_names():
                console.print(f"[bold blue]- Database: {db_name}[/]")
                db = self.client[db_name]
                collections = db.list_collection_names()
                for collection_name in collections:
                    console.print(f"[purple]  -- {collection_name}[/]")
        except Exception as e:
            logger.error(f"Error showing databases and collections: {e}")
            raise

    def set_database(self, database_name):
        """Changes the currently used database."""
        self.database_name = database_name
        self.db = self.client[database_name]

    def set_collection(self, collection_name):
        """Changes the currently used collection."""
        self.collection_name = collection_name
        self.collection = self.db[collection_name]
