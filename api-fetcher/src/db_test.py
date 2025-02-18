import configparser
from pymongo import MongoClient

config = configparser.ConfigParser()
config.read('../config.ini')

db_host = config['database']['host']
db_port = config.getint('database', 'port')
db_user = config['database']['username']
db_pass = config['database']['password']
db_name = "testdb"

client = MongoClient(f"mongodb://{db_user}:{db_pass}@{db_host}:{db_port}")
db = client.get_database(db_name)
collection = db.testcol

query = {'name': 'test'}
collection.update_one(query, {'$set': {'value': 'aaa'}}, upsert=True)
