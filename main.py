from fastapi import FastAPI, HTTPException, Depends
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.models import OAuthFlowAuthorizationCode
from fastapi.openapi.models import OAuthFlows
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.responses import JSONResponse
from bson import ObjectId, json_util
import json
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
import os
import ssl
import certifi
from models import Stock, StockDetail

load_dotenv()

app = FastAPI()


async def get_mongo_db():
    mongo_uri = f"mongodb+srv://{os.environ['MONGO_USERNAME']}:{os.environ['MONGO_PASSWORD']}@{os.environ['MONGODB_CLUSTER']}/{os.environ['DATABASE_NAME']}?retryWrites=true&w=majority"
    client = AsyncIOMotorClient(
        mongo_uri
    )
    db = client.Stocks['US_S&P500']
    yield db
    client.close()


@app.get("/")
def read_root():
    return {"message": "Welcome to the homepage"}


@app.get("/Stocks/US_S&P500", response_model=list[Stock])
async def get_all_stocks(db: AsyncIOMotorClient = Depends(get_mongo_db)):
    projection = {
        '_id': 0,       # Exclude the '_id' field
        'AnnualIncomeStatements': 0,
        'AnnualBalanceSheets': 0,
        'QuarterlyIncomeStatements': 0,
        'QuarterlyBalanceSheets': 0,
    }
    stocks = await db.find({}, projection=projection).to_list(length=None)

    # Convert ObjectId to string in each document
    stocks = [ {**stock} for stock in stocks ]
    
    # Use jsonable_encoder to get a JSON-serializable representation
    stocks_json = jsonable_encoder(stocks)

    # Replace NaN and Infinity with strings
    stock_json = json.dumps(stocks_json).replace("NaN", '"NaN"').replace("Infinity", '"Infinity"')

    # Convert the JSON string to a Python object
    stocks_dict = json.loads(stock_json)

    # Return JSON response
    return JSONResponse(content=stocks_dict, media_type="application/json")



@app.get("/Stocks/US_S&P500/{symbol}", response_model=StockDetail)
async def get_stock_by_symbol(
    symbol: str, db: AsyncIOMotorClient = Depends(get_mongo_db)
):
    stock = await db.find_one({"Symbol": symbol})
    if stock:
        # Create a StockDetail instance
        stock_detail = StockDetail(**stock)

        # Use jsonable_encoder to get a JSON-serializable representation
        stock_dict = jsonable_encoder(stock_detail)

        # Replace NaN and Infinity with strings
        stock_json = json.dumps(stock_dict).replace("NaN", '"NaN"').replace("Infinity", '"Infinity"')

        # Convert the JSON string to a Python object
        stock_dict = json.loads(stock_json)

        # Return a more readable JSON response
        return stock_dict
    else:
        raise HTTPException(status_code=404, detail="Stock not found")