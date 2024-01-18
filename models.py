from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime

class Stock(BaseModel):
    Symbol: str
    MarketCap_Billions: float
    TrailingPE: float
    ForwardPE: float
    TrailingAnnualDividendYield: float
    FiveYearAvgDividendYield: float
    PayoutRatio: float
    ROE: Optional[float]
    ROA: Optional[float]
    ROE_TTM: Optional[float]
    ROA_TTM: Optional[float]

    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat(),
        }

class StockDetail(Stock):
    # id: str
    AnnualIncomeStatements: List[dict]
    AnnualBalanceSheets: List[dict]
    QuarterlyIncomeStatements: List[dict]
    QuarterlyBalanceSheets: List[dict]