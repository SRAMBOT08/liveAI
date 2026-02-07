"""
Pathway State Management
Stateful transformations for price tracking and change detection
"""
import pathway as pw
from .schemas import MarketEventSchema, PriceStateSchema


def compute_price_state(market_events: pw.Table) -> pw.Table:
    """
    Compute stateful price changes
    
    Args:
        market_events: Stream of market events
    
    Returns:
        Table with price state including previous price and changes
    """
    
    # Group by instrument to maintain state per instrument
    grouped = market_events.groupby(market_events.instrument_id)
    
    # Use Pathway's stateful operations to track previous price
    # Using reduce to maintain running state
    price_state = grouped.reduce(
        grouped.instrument_id,
        timestamp=pw.reducers.latest(grouped.timestamp),
        price=pw.reducers.latest(grouped.price),
        price_previous=pw.reducers.nth_prev(grouped.price, 1),
    )
    
    # Compute price changes
    price_state = price_state.select(
        pw.this.instrument_id,
        pw.this.timestamp,
        pw.this.price,
        price_previous=pw.coalesce(pw.this.price_previous, pw.this.price),
    )
    
    price_state = price_state.select(
        pw.this.instrument_id,
        pw.this.timestamp,
        pw.this.price,
        pw.this.price_previous,
        price_change=pw.this.price - pw.this.price_previous,
        price_change_pct=pw.if_else(
            pw.this.price_previous != 0.0,
            ((pw.this.price - pw.this.price_previous) / pw.this.price_previous) * 100.0,
            0.0
        )
    )
    
    return price_state


def get_latest_price(price_state: pw.Table, instrument_id: str) -> pw.Table:
    """
    Get latest price for specific instrument
    
    Args:
        price_state: Price state table
        instrument_id: Instrument to filter
    
    Returns:
        Filtered table with latest price
    """
    return price_state.filter(price_state.instrument_id == instrument_id)
