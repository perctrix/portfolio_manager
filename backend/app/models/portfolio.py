from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PortfolioType(str, Enum):
    TRANSACTION = "transaction"
    SNAPSHOT = "snapshot"

class Portfolio(BaseModel):
    id: str
    name: str
    type: PortfolioType
    base_currency: str = "USD"
    created_at: datetime = datetime.now()
    description: Optional[str] = None
