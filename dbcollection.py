from pymongo import MongoClient  #type: ignore
from urllib.parse import quote_plus
from settings import __SETTINGS__
from urllib.parse import quote_plus 

class MongoDBHandler:
    def __init__(self, uri=__SETTINGS__.DB.CONNECTION_STRING, db_name=__SETTINGS__.DB.DB_NAME): # type: ignore
        encoded_password = quote_plus(__SETTINGS__.DB.PASSWORD)   # type: ignore
        uri = uri.replace("<db_password>", encoded_password )

        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def get_collection_names(self):
        """Returns a list of all collection names in the database."""
        return self.db.list_collection_names()

    def get_collection(self, collection_name):
        """Returns a reference to a specific collection."""
        return self.db[collection_name]

    def close_connection(self):
        self.client.close()