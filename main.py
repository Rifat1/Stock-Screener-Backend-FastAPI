from typing import List
from fastapi import FastAPI, HTTPException
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

mongo_uri = f"mongodb+srv://{os.environ['MONGO_USERNAME']}:{os.environ['MONGO_PASSWORD']}@{os.environ['MONGODB_CLUSTER']}/{os.environ['DATABASE_NAME']}?retryWrites=true&w=majority"

class DatabaseManager:
    def __init__(self):
        self.db_client = None
        self.db = None
        self.collection = None
    
    async def initialize_database(self):
        try:
            self.db_client = AsyncIOMotorClient(mongo_uri, io_loop=asyncio.get_event_loop())
            self.db = self.db_client[os.environ['DATABASE_NAME']]
            self.collection = self.db['US_S&P500']
        except Exception as e:
            print(f"Error initializing database: {str(e)}")

    async def test_connection(self):
        try:
            db_client = AsyncIOMotorClient(mongo_uri, io_loop=asyncio.get_event_loop())
            db = db_client[os.environ['DATABASE_NAME']] 
            self.collection = db['US_S&P500'] 
            result = await self.collection.count_documents.__call__({})
            return f"Connected! Found {result} documents."
        except Exception as e:
            return f"Not Connected - Error: {e}"
    @property
    async def get_collection(self):
        if not self.collection or self.db_client.is_closed:
            await self.initialize_database()
        return self.collection    

database_manager = DatabaseManager()

# db = db_client[os.environ['DATABASE_NAME']]
# collection = db['US_S&P500']

# Define a projection excluding the 'Annual Income Statements' field
projection = {"Annual Income Statements": False, 'Annual Balance Sheets': False, 'Quarterly Income Statements': False, 'Quarterly Balance Sheets': False}

@app.get("/healthz")
async def read_root():
    response = await database_manager.test_connection()
    return {"message": response}

@app.get("/", tags=["Home"])
def read_root():
    return {
        "message": "Welcome to Stock Screener!"
    }


@app.get("/Stocks/US_S&P500", response_model=List[dict], tags=["Stocks"])
async def read_stocks():
    collection = await database_manager.get_collection
    cursor = database_manager.collection.find(projection = projection)
    return await cursor.to_list(length=None)


@app.get("/Stocks/US_S&P500/{symbol}", response_model=dict, tags=["Stocks"])
async def read_stock(symbol: str):
    doc = await collection.find_one({"Symbol": symbol})
    if not doc:
        raise HTTPException(status_code=404, detail="Stock not found.")
    else:
        del doc["_id"]
        return doc