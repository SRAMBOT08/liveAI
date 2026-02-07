"""
Black-76 Model and Greeks Calculation
Deterministic option pricing and risk metrics computation
"""
import numpy as np
from scipy.stats import norm
from typing import Tuple
from datetime import datetime

from config.instruments import DEFAULT_OPTION


def black_76_price(
    futures_price: float,
    strike: float,
    time_to_expiration: float,
    risk_free_rate: float,
    volatility: float,
    option_type: str = "call"
) -> float:
    """
    Black-76 option pricing model for futures options
    
    Args:
        futures_price: Current futures price
        strike: Option strike price
        time_to_expiration: Time to expiration in years
        risk_free_rate: Risk-free interest rate (annualized)
        volatility: Implied volatility (annualized)
        option_type: "call" or "put"
    
    Returns:
        Option theoretical price
    """
    
    if time_to_expiration <= 0:
        # Option expired
        if option_type == "call":
            return max(futures_price - strike, 0.0)
        else:
            return max(strike - futures_price, 0.0)
    
    # Black-76 formula components
    d1 = (np.log(futures_price / strike) + (volatility ** 2 / 2) * time_to_expiration) / \
         (volatility * np.sqrt(time_to_expiration))
    d2 = d1 - volatility * np.sqrt(time_to_expiration)
    
    discount = np.exp(-risk_free_rate * time_to_expiration)
    
    if option_type == "call":
        price = discount * (futures_price * norm.cdf(d1) - strike * norm.cdf(d2))
    else:  # put
        price = discount * (strike * norm.cdf(-d2) - futures_price * norm.cdf(-d1))
    
    return price


def compute_greeks(
    futures_price: float,
    strike: float,
    time_to_expiration: float,
    risk_free_rate: float,
    volatility: float,
    option_type: str = "call"
) -> dict:
    """
    Compute all Greeks using Black-76 model
    
    Returns:
        Dictionary with delta, gamma, theta, vega, rho
    """
    
    if time_to_expiration <= 0.0001:
        time_to_expiration = 0.0001  # Prevent division by zero
    
    # Compute d1 and d2
    d1 = (np.log(futures_price / strike) + (volatility ** 2 / 2) * time_to_expiration) / \
         (volatility * np.sqrt(time_to_expiration))
    d2 = d1 - volatility * np.sqrt(time_to_expiration)
    
    discount = np.exp(-risk_free_rate * time_to_expiration)
    
    # Delta
    if option_type == "call":
        delta = discount * norm.cdf(d1)
    else:
        delta = -discount * norm.cdf(-d1)
    
    # Gamma (same for call and put)
    gamma = (discount * norm.pdf(d1)) / (futures_price * volatility * np.sqrt(time_to_expiration))
    
    # Vega (same for call and put)
    vega = futures_price * discount * norm.pdf(d1) * np.sqrt(time_to_expiration) / 100.0  # divide by 100 for percentage
    
    # Theta
    if option_type == "call":
        theta = (
            -futures_price * discount * norm.pdf(d1) * volatility / (2 * np.sqrt(time_to_expiration))
            - risk_free_rate * futures_price * norm.cdf(d1) * discount
            + risk_free_rate * strike * discount * norm.cdf(d2)
        ) / 365.0  # Per day
    else:
        theta = (
            -futures_price * discount * norm.pdf(d1) * volatility / (2 * np.sqrt(time_to_expiration))
            + risk_free_rate * futures_price * norm.cdf(-d1) * discount
            - risk_free_rate * strike * discount * norm.cdf(-d2)
        ) / 365.0  # Per day
    
    # Rho
    if option_type == "call":
        rho = -time_to_expiration * (
            futures_price * norm.cdf(d1) - strike * norm.cdf(d2)
        ) * discount / 100.0  # divide by 100 for percentage
    else:
        rho = -time_to_expiration * (
            strike * norm.cdf(-d2) - futures_price * norm.cdf(-d1)
        ) * discount / 100.0
    
    return {
        "delta": float(delta),
        "gamma": float(gamma),
        "theta": float(theta),
        "vega": float(vega),
        "rho": float(rho)
    }


def calculate_option_greeks(
    underlying_price: float,
    current_time: datetime = None,
    volatility: float = 0.20  # 20% default IV
) -> dict:
    """
    Calculate Greeks for the default option contract
    
    Args:
        underlying_price: Current futures price
        current_time: Current timestamp (for time to expiration)
        volatility: Implied volatility
    
    Returns:
        Dictionary with option_price and all Greeks
    """
    if current_time is None:
        current_time = datetime.now()
    
    option = DEFAULT_OPTION
    tte = option.time_to_expiration_years(current_time)
    
    # Calculate option price
    option_price = black_76_price(
        futures_price=underlying_price,
        strike=option.strike,
        time_to_expiration=tte,
        risk_free_rate=option.risk_free_rate,
        volatility=volatility,
        option_type=option.option_type
    )
    
    # Calculate Greeks
    greeks = compute_greeks(
        futures_price=underlying_price,
        strike=option.strike,
        time_to_expiration=tte,
        risk_free_rate=option.risk_free_rate,
        volatility=volatility,
        option_type=option.option_type
    )
    
    return {
        "option_price": option_price,
        **greeks
    }


def shock_greeks(
    base_price: float,
    shock_percent: float,
    current_time: datetime = None,
    volatility: float = 0.20
) -> dict:
    """
    Calculate Greeks for a shocked price scenario
    
    Args:
        base_price: Current futures price
        shock_percent: Shock as decimal (e.g., 0.05 for +5%)
        current_time: Current timestamp
        volatility: Implied volatility
    
    Returns:
        Greeks dictionary for shocked scenario
    """
    shocked_price = base_price * (1.0 + shock_percent)
    return calculate_option_greeks(shocked_price, current_time, volatility)
