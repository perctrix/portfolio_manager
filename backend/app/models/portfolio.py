from enum import Enum, IntEnum
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class PortfolioType(str, Enum):
    TRANSACTION = "transaction"
    SNAPSHOT = "snapshot"


class PaymentFrequency(IntEnum):
    ZERO_COUPON = 0
    ANNUAL = 1
    SEMI_ANNUAL = 2
    QUARTERLY = 4
    MONTHLY = 12


class BondPosition(BaseModel):
    id: str
    name: str
    face_value: float
    coupon_rate: float  # as percentage, e.g., 2.5 for 2.5%
    maturity_date: date
    payment_frequency: PaymentFrequency
    purchase_price: float  # clean price as % of face value
    purchase_quantity: float
    purchase_date: date
    current_price: Optional[float] = None
    currency: Optional[str] = None

class Portfolio(BaseModel):
    id: str
    name: str
    type: PortfolioType
    base_currency: str = "USD"
    created_at: datetime = datetime.now()
    description: Optional[str] = None
