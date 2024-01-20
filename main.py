from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
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

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:3000",
    "https://127.0.0.1:3000",
    "http://localhost:8000", 
    "https://localhost:8000"
    "http://localhost:80"
    "https://localhost:80"
    "http://54.166.200.70:80"
    "https://54.166.200.70:80"
    # Add other frontend URLs as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)
 
async def startup_event():
    redis_connection = redis.from_url("redis://redis:6379/0", encoding="utf8")
    await FastAPILimiter.init(redis_connection)

async def shutdown_event():
    await FastAPILimiter.close()

app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)


async def get_mongo_db():
    mongo_uri = f"mongodb+srv://{os.environ['MONGO_USERNAME']}:{os.environ['MONGO_PASSWORD']}@{os.environ['MONGODB_CLUSTER']}/{os.environ['DATABASE_NAME']}?retryWrites=true&w=majority"
    client = AsyncIOMotorClient(
        mongo_uri
    )
    db = client.Stocks['US_S&P500']
    yield db
    client.close()




@app.get("/", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
def read_root():
    return {"message": "Welcome to StockDat, an index based stock market screener"}



# /stocks/SP500
@app.get("/stocks/{index_name}", response_model=list[Stock], dependencies=[Depends(RateLimiter(times=2, seconds=5)), Depends(RateLimiter(times=3000, hours=24))])
async def get_stocks(
    page: int = Query(1, ge=1),  # Default page is 1
    page_size: int = Query(20, ge=5, le=40),  # Default page size is 20, limit to 40
    db: AsyncIOMotorClient = Depends(get_mongo_db)
):
    skip = (page - 1) * page_size
    limit = page_size

    projection = {
        '_id': 0,       # Exclude the '_id' field
        'AnnualIncomeStatements': 0,
        'AnnualBalanceSheets': 0,
        'QuarterlyIncomeStatements': 0,
        'QuarterlyBalanceSheets': 0,
    }
    # Modify the query to include a sort operation on the 'ROE' field in descending order
    stocks = await db.find({}, projection=projection).sort("MarketCap_Billions", -1).skip(skip).limit(limit).to_list(length=None)

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





@app.get("/Stocks/US_S&P500/{symbol}", response_model=StockDetail, dependencies=[Depends(RateLimiter(times=2, seconds=5)), Depends(RateLimiter(times=30, hours=24))])
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