"""
Data fetcher module for investment trust portfolio analysis tool.
Handles dummy data generation, SQLite caching, and data preprocessing.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import streamlit as st
import os

# Database path
DB_PATH = "fund_data_cache.db"

# Fund definitions (simulating MUA API fund data)
FUND_DEFINITIONS = {
    "MUA001": {
        "name": "eMAXIS Slim 全世界株式（オール・カントリー）",
        "category": "global_equity",
        "base_return": 0.08,
        "volatility": 0.18,
        "dividend_yield": 0.02
    },
    "MUA002": {
        "name": "eMAXIS Slim 米国株式（S&P500）",
        "category": "us_equity",
        "base_return": 0.10,
        "volatility": 0.20,
        "dividend_yield": 0.015
    },
    "MUA003": {
        "name": "eMAXIS Slim 先進国株式インデックス",
        "category": "developed_equity",
        "base_return": 0.07,
        "volatility": 0.17,
        "dividend_yield": 0.018
    },
    "MUA004": {
        "name": "eMAXIS Slim 国内株式（TOPIX）",
        "category": "japan_equity",
        "base_return": 0.05,
        "volatility": 0.16,
        "dividend_yield": 0.022
    },
    "MUA005": {
        "name": "eMAXIS Slim 新興国株式インデックス",
        "category": "emerging_equity",
        "base_return": 0.06,
        "volatility": 0.25,
        "dividend_yield": 0.025
    },
    "MUA006": {
        "name": "eMAXIS Slim 先進国債券インデックス",
        "category": "developed_bond",
        "base_return": 0.02,
        "volatility": 0.06,
        "dividend_yield": 0.03
    },
    "MUA007": {
        "name": "eMAXIS Slim 国内債券インデックス",
        "category": "japan_bond",
        "base_return": 0.01,
        "volatility": 0.03,
        "dividend_yield": 0.01
    },
    "MUA008": {
        "name": "eMAXIS Slim バランス（8資産均等型）",
        "category": "balanced",
        "base_return": 0.04,
        "volatility": 0.10,
        "dividend_yield": 0.02
    }
}

# Crisis period definition (COVID-19 crash)
CRISIS_PERIOD = {
    "name": "COVID-19 Crash",
    "start": datetime(2020, 2, 19),
    "end": datetime(2020, 3, 23)
}


def init_database():
    """Initialize SQLite database for caching fund data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fund_prices (
            fund_id TEXT,
            date TEXT,
            nav REAL,
            dividend REAL,
            PRIMARY KEY (fund_id, date)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache_metadata (
            fund_id TEXT PRIMARY KEY,
            last_updated TEXT,
            start_date TEXT,
            end_date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


def generate_dummy_fund_data(
    fund_id: str,
    start_date: datetime,
    end_date: datetime,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate dummy time series data for a fund simulating MUA API response.
    
    Args:
        fund_id: Fund identifier
        start_date: Start date for data generation
        end_date: End date for data generation
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with columns: date, nav, dividend
    """
    if fund_id not in FUND_DEFINITIONS:
        raise ValueError(f"Unknown fund ID: {fund_id}")
    
    fund_info = FUND_DEFINITIONS[fund_id]
    
    # Set seed based on fund_id for reproducibility
    if seed is None:
        seed = hash(fund_id) % (2**32)
    np.random.seed(seed)
    
    # Generate business days
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    n_days = len(dates)
    
    if n_days == 0:
        return pd.DataFrame(columns=['date', 'nav', 'dividend'])
    
    # Parameters
    annual_return = fund_info['base_return']
    annual_volatility = fund_info['volatility']
    dividend_yield = fund_info['dividend_yield']
    
    # Daily parameters
    daily_return = annual_return / 252
    daily_volatility = annual_volatility / np.sqrt(252)
    
    # Generate returns with regime changes for realism
    returns = np.random.normal(daily_return, daily_volatility, n_days)
    
    # Add crisis period effects (COVID-19 crash simulation)
    crisis_start = CRISIS_PERIOD['start']
    crisis_end = CRISIS_PERIOD['end']
    
    for i, date in enumerate(dates):
        date_dt = date.to_pydatetime()
        if crisis_start <= date_dt <= crisis_end:
            # Increase volatility and negative bias during crisis
            crisis_factor = -0.02 if fund_info['category'] in ['global_equity', 'us_equity', 'developed_equity', 'japan_equity', 'emerging_equity'] else -0.005
            returns[i] = np.random.normal(crisis_factor, daily_volatility * 2.5)
    
    # Calculate NAV (starting at 10000)
    initial_nav = 10000
    nav_series = initial_nav * np.cumprod(1 + returns)
    
    # Generate dividends (quarterly, on specific months)
    dividends = np.zeros(n_days)
    quarterly_dividend = (initial_nav * dividend_yield) / 4
    
    for i, date in enumerate(dates):
        # Dividends on last business day of March, June, September, December
        if date.month in [3, 6, 9, 12]:
            next_date = dates[i + 1] if i + 1 < n_days else None
            if next_date is None or next_date.month != date.month:
                dividends[i] = quarterly_dividend * (nav_series[i] / initial_nav)
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'nav': nav_series,
        'dividend': dividends
    })
    
    return df


def save_to_cache(fund_id: str, df: pd.DataFrame):
    """Save fund data to SQLite cache."""
    conn = sqlite3.connect(DB_PATH)
    
    # Convert date to string for SQLite
    df_to_save = df.copy()
    df_to_save['date'] = df_to_save['date'].dt.strftime('%Y-%m-%d')
    df_to_save['fund_id'] = fund_id
    
    # Delete existing data for this fund
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fund_prices WHERE fund_id = ?", (fund_id,))
    
    # Insert new data
    df_to_save[['fund_id', 'date', 'nav', 'dividend']].to_sql(
        'fund_prices', conn, if_exists='append', index=False
    )
    
    # Update metadata
    cursor.execute('''
        INSERT OR REPLACE INTO cache_metadata (fund_id, last_updated, start_date, end_date)
        VALUES (?, ?, ?, ?)
    ''', (
        fund_id,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        df['date'].min().strftime('%Y-%m-%d'),
        df['date'].max().strftime('%Y-%m-%d')
    ))
    
    conn.commit()
    conn.close()


def load_from_cache(fund_id: str) -> Optional[pd.DataFrame]:
    """Load fund data from SQLite cache."""
    if not os.path.exists(DB_PATH):
        return None
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        df = pd.read_sql_query(
            "SELECT date, nav, dividend FROM fund_prices WHERE fund_id = ? ORDER BY date",
            conn,
            params=(fund_id,)
        )
        
        if df.empty:
            return None
        
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception:
        return None
    finally:
        conn.close()


def is_cache_valid(fund_id: str, start_date: datetime, end_date: datetime) -> bool:
    """Check if cached data covers the requested date range."""
    if not os.path.exists(DB_PATH):
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT start_date, end_date FROM cache_metadata WHERE fund_id = ?",
        (fund_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result is None:
        return False
    
    cached_start = datetime.strptime(result[0], '%Y-%m-%d')
    cached_end = datetime.strptime(result[1], '%Y-%m-%d')
    
    return cached_start <= start_date and cached_end >= end_date


@st.cache_data(ttl=3600)
def fetch_fund_data(
    fund_id: str,
    start_date: datetime,
    end_date: datetime,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Fetch fund data with caching support.
    
    This function simulates fetching data from MUA API.
    In production, this would make actual API calls.
    
    Args:
        fund_id: Fund identifier
        start_date: Start date for data
        end_date: End date for data
        use_cache: Whether to use SQLite cache
        
    Returns:
        DataFrame with fund price data
    """
    init_database()
    
    # Check cache first
    if use_cache and is_cache_valid(fund_id, start_date, end_date):
        cached_data = load_from_cache(fund_id)
        if cached_data is not None:
            mask = (cached_data['date'] >= start_date) & (cached_data['date'] <= end_date)
            return cached_data[mask].reset_index(drop=True)
    
    # Generate dummy data (simulating API call)
    df = generate_dummy_fund_data(fund_id, start_date, end_date)
    
    # Save to cache
    if use_cache:
        save_to_cache(fund_id, df)
    
    return df


@st.cache_data(ttl=3600)
def fetch_multiple_funds(
    fund_ids: List[str],
    start_date: datetime,
    end_date: datetime
) -> Dict[str, pd.DataFrame]:
    """
    Fetch data for multiple funds.
    
    Args:
        fund_ids: List of fund identifiers
        start_date: Start date for data
        end_date: End date for data
        
    Returns:
        Dictionary mapping fund_id to DataFrame
    """
    result = {}
    for fund_id in fund_ids:
        result[fund_id] = fetch_fund_data(fund_id, start_date, end_date)
    return result


def calculate_total_return(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily total return (dividend reinvestment basis).
    
    Args:
        df: DataFrame with columns: date, nav, dividend
        
    Returns:
        DataFrame with additional columns: daily_return, cumulative_return, total_return_index
    """
    df = df.copy()
    
    # Calculate price return
    df['price_return'] = df['nav'].pct_change()
    
    # Calculate dividend return (dividend / previous day NAV)
    df['dividend_return'] = df['dividend'] / df['nav'].shift(1)
    df['dividend_return'] = df['dividend_return'].fillna(0)
    
    # Total daily return
    df['daily_return'] = df['price_return'] + df['dividend_return']
    df['daily_return'] = df['daily_return'].fillna(0)
    
    # Cumulative return (total return index starting at 1)
    df['total_return_index'] = (1 + df['daily_return']).cumprod()
    
    # Cumulative return percentage
    df['cumulative_return'] = df['total_return_index'] - 1
    
    return df


def prepare_analysis_data(
    fund_ids: List[str],
    start_date: datetime,
    end_date: datetime
) -> Dict[str, pd.DataFrame]:
    """
    Prepare fund data for analysis with total returns calculated.
    
    Args:
        fund_ids: List of fund identifiers
        start_date: Start date for analysis
        end_date: End date for analysis
        
    Returns:
        Dictionary mapping fund_id to processed DataFrame
    """
    raw_data = fetch_multiple_funds(fund_ids, start_date, end_date)
    
    processed_data = {}
    for fund_id, df in raw_data.items():
        processed_data[fund_id] = calculate_total_return(df)
    
    return processed_data


def get_fund_list() -> Dict[str, str]:
    """
    Get list of available funds.
    
    Returns:
        Dictionary mapping fund_id to fund name
    """
    return {fund_id: info['name'] for fund_id, info in FUND_DEFINITIONS.items()}


def get_fund_info(fund_id: str) -> Dict:
    """
    Get detailed information about a fund.
    
    Args:
        fund_id: Fund identifier
        
    Returns:
        Dictionary with fund information
    """
    if fund_id not in FUND_DEFINITIONS:
        raise ValueError(f"Unknown fund ID: {fund_id}")
    return FUND_DEFINITIONS[fund_id]


def get_crisis_period() -> Dict:
    """Get the defined crisis period."""
    return CRISIS_PERIOD


def create_returns_matrix(
    processed_data: Dict[str, pd.DataFrame],
    fund_ids: List[str]
) -> pd.DataFrame:
    """
    Create a matrix of daily returns for multiple funds.
    
    Args:
        processed_data: Dictionary of processed fund data
        fund_ids: List of fund IDs to include
        
    Returns:
        DataFrame with dates as index and fund returns as columns
    """
    returns_dict = {}
    
    for fund_id in fund_ids:
        if fund_id in processed_data:
            df = processed_data[fund_id]
            returns_dict[fund_id] = df.set_index('date')['daily_return']
    
    returns_matrix = pd.DataFrame(returns_dict)
    returns_matrix = returns_matrix.dropna()
    
    return returns_matrix
