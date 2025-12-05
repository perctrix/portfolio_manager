"""Bond valuation utilities for fixed-rate and zero-coupon bonds.

Uses 30/360 day count convention for accrued interest calculations.
"""

from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Optional
from app.models.portfolio import BondPosition, PaymentFrequency


def get_months_per_period(frequency: PaymentFrequency) -> int:
    """Get number of months between coupon payments.

    Args:
        frequency: Payment frequency enum value

    Returns:
        Number of months per coupon period
    """
    if frequency == PaymentFrequency.ZERO_COUPON:
        return 0
    elif frequency == PaymentFrequency.ANNUAL:
        return 12
    elif frequency == PaymentFrequency.SEMI_ANNUAL:
        return 6
    elif frequency == PaymentFrequency.QUARTERLY:
        return 3
    elif frequency == PaymentFrequency.MONTHLY:
        return 1
    return 0


def get_coupon_dates(
    maturity_date: date,
    payment_frequency: PaymentFrequency,
    start_date: date,
    end_date: date
) -> list[date]:
    """Generate all coupon payment dates within a date range.

    Args:
        maturity_date: Bond maturity date
        payment_frequency: Number of coupons per year
        start_date: Start of date range
        end_date: End of date range

    Returns:
        List of coupon payment dates within the range
    """
    if payment_frequency == PaymentFrequency.ZERO_COUPON:
        return []

    months_per_period = get_months_per_period(payment_frequency)
    if months_per_period == 0:
        return []

    coupon_dates: list[date] = []
    current = maturity_date

    while current > start_date:
        current = current - relativedelta(months=months_per_period)

    if current < start_date:
        current = current + relativedelta(months=months_per_period)

    while current <= end_date:
        if current >= start_date and current <= maturity_date:
            coupon_dates.append(current)
        current = current + relativedelta(months=months_per_period)

    return sorted(coupon_dates)


def get_last_coupon_date(
    maturity_date: date,
    payment_frequency: PaymentFrequency,
    reference_date: date
) -> Optional[date]:
    """Calculate the most recent coupon payment date before or on reference_date.

    Args:
        maturity_date: Bond maturity date
        payment_frequency: Number of coupons per year
        reference_date: Date to find last coupon before

    Returns:
        Last coupon date, or None for zero-coupon bonds
    """
    if payment_frequency == PaymentFrequency.ZERO_COUPON:
        return None

    months_per_period = get_months_per_period(payment_frequency)
    if months_per_period == 0:
        return None

    current = maturity_date
    while current > reference_date:
        current = current - relativedelta(months=months_per_period)

    return current


def get_next_coupon_date(
    maturity_date: date,
    payment_frequency: PaymentFrequency,
    reference_date: date
) -> Optional[date]:
    """Calculate the next coupon payment date after reference_date.

    Args:
        maturity_date: Bond maturity date
        payment_frequency: Number of coupons per year
        reference_date: Date to find next coupon after

    Returns:
        Next coupon date, or None for zero-coupon or if past maturity
    """
    if payment_frequency == PaymentFrequency.ZERO_COUPON:
        return None

    if reference_date >= maturity_date:
        return None

    last_coupon = get_last_coupon_date(maturity_date, payment_frequency, reference_date)
    if last_coupon is None:
        return None

    months_per_period = get_months_per_period(payment_frequency)
    next_coupon = last_coupon + relativedelta(months=months_per_period)

    if next_coupon > maturity_date:
        return maturity_date

    return next_coupon


def days_30_360(start: date, end: date) -> int:
    """Calculate days between two dates using 30/360 convention.

    Args:
        start: Start date
        end: End date

    Returns:
        Number of days using 30/360 convention
    """
    d1 = min(start.day, 30)
    d2 = end.day if d1 < 30 else min(end.day, 30)

    return (
        360 * (end.year - start.year)
        + 30 * (end.month - start.month)
        + (d2 - d1)
    )


def calculate_accrued_interest(
    bond: BondPosition,
    valuation_date: date
) -> float:
    """Calculate accrued interest for a bond position.

    Uses 30/360 day count convention.

    Args:
        bond: Bond position
        valuation_date: Date to calculate accrued interest for

    Returns:
        Total accrued interest for the position
    """
    if bond.payment_frequency == PaymentFrequency.ZERO_COUPON:
        return 0.0

    if valuation_date >= bond.maturity_date:
        return 0.0

    last_coupon = get_last_coupon_date(
        bond.maturity_date,
        bond.payment_frequency,
        valuation_date
    )
    if last_coupon is None:
        return 0.0

    days = days_30_360(last_coupon, valuation_date)

    annual_coupon = bond.face_value * (bond.coupon_rate / 100.0)
    accrued_per_bond = annual_coupon * days / 360.0

    return accrued_per_bond * bond.purchase_quantity


def calculate_accrued_interest_per_100(
    bond: BondPosition,
    valuation_date: date
) -> float:
    """Calculate accrued interest per 100 face value.

    Args:
        bond: Bond position
        valuation_date: Date to calculate accrued interest for

    Returns:
        Accrued interest per 100 face value
    """
    if bond.payment_frequency == PaymentFrequency.ZERO_COUPON:
        return 0.0

    if valuation_date >= bond.maturity_date:
        return 0.0

    last_coupon = get_last_coupon_date(
        bond.maturity_date,
        bond.payment_frequency,
        valuation_date
    )
    if last_coupon is None:
        return 0.0

    days = days_30_360(last_coupon, valuation_date)

    accrued_per_100 = bond.coupon_rate * days / 360.0

    return accrued_per_100


def is_matured(bond: BondPosition, valuation_date: date) -> bool:
    """Check if a bond has matured.

    Args:
        bond: Bond position
        valuation_date: Date to check

    Returns:
        True if bond has matured
    """
    return valuation_date >= bond.maturity_date


def calculate_bond_value(
    bond: BondPosition,
    valuation_date: date,
    clean_price: Optional[float] = None
) -> float:
    """Calculate current market value of a bond position.

    Args:
        bond: Bond position
        valuation_date: Date to calculate value for
        clean_price: Override clean price (as % of face), uses bond's price if None

    Returns:
        Total market value of the position
    """
    if valuation_date < bond.purchase_date:
        return 0.0

    if valuation_date >= bond.maturity_date:
        return bond.face_value * bond.purchase_quantity

    price = clean_price if clean_price is not None else (
        bond.current_price if bond.current_price is not None else bond.purchase_price
    )

    accrued_per_100 = calculate_accrued_interest_per_100(bond, valuation_date)
    dirty_price = price + accrued_per_100

    return (dirty_price / 100.0) * bond.face_value * bond.purchase_quantity


def generate_coupon_payments(
    bond: BondPosition,
    start_date: date,
    end_date: date
) -> list[tuple[date, float]]:
    """Generate coupon payment dates and amounts within a date range.

    Args:
        bond: Bond position
        start_date: Start of date range
        end_date: End of date range

    Returns:
        List of (date, amount) tuples for each coupon payment
    """
    if bond.payment_frequency == PaymentFrequency.ZERO_COUPON:
        return []

    coupon_dates = get_coupon_dates(
        bond.maturity_date,
        bond.payment_frequency,
        start_date,
        end_date
    )

    coupon_per_period = (
        bond.face_value
        * (bond.coupon_rate / 100.0)
        * bond.purchase_quantity
        / int(bond.payment_frequency)
    )

    return [(d, coupon_per_period) for d in coupon_dates if d >= bond.purchase_date]


def calculate_bond_cost_basis(bond: BondPosition) -> float:
    """Calculate total cost basis for a bond position.

    The cost basis is the dirty price (clean price + accrued interest at purchase),
    which represents the actual cash outlay when purchasing the bond.

    Args:
        bond: Bond position

    Returns:
        Total cost basis (dirty price at purchase * face value * quantity / 100)
    """
    accrued_per_100 = calculate_accrued_interest_per_100(bond, bond.purchase_date)
    dirty_price = bond.purchase_price + accrued_per_100
    return (dirty_price / 100.0) * bond.face_value * bond.purchase_quantity
