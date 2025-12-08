"""
Securities Master Database
Provides ticker/fund lookup functionality with asset classification and account type support.
"""

import sqlite3
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
import pandas as pd

# Database path
SECURITIES_DB_PATH = "securities_master.db"

# Asset classes
ASSET_CLASSES = {
    'cash': '現預金',
    'domestic_stock': '国内株式',
    'foreign_stock': '外国株式',
    'domestic_bond': '国内債券',
    'foreign_bond': '外国債券',
    'reit': 'REIT',
    'commodity': 'コモディティ',
    'balanced': 'バランス型',
    'insurance': '保険（貯蓄性）',
}

# Account types
ACCOUNT_TYPES = {
    'tokutei': '特定口座',
    'nisa_tsumitate': 'NISAつみたて投資枠',
    'nisa_growth': 'NISA成長投資枠',
    'nisa_old': '旧NISA',
    'ideco': 'iDeCo',
    'general': '一般口座',
}

# Regions
REGIONS = {
    'japan': '日本',
    'us': '米国',
    'developed': '先進国',
    'emerging': '新興国',
    'global': '全世界',
}


@dataclass
class Security:
    """Represents a security (stock, fund, etc.)."""
    ticker: str
    name: str
    asset_class: str
    region: str
    currency: str
    expected_return: float  # Annual expected return
    volatility: float       # Annual volatility
    dividend_yield: float   # Annual dividend yield
    expense_ratio: float    # Annual expense ratio (for funds)
    nisa_eligible: bool     # Whether eligible for NISA
    tsumitate_eligible: bool  # Whether eligible for NISA tsumitate


def init_securities_database():
    """Initialize the securities master database."""
    conn = sqlite3.connect(SECURITIES_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS securities (
            ticker TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            asset_class TEXT NOT NULL,
            region TEXT,
            currency TEXT DEFAULT 'JPY',
            expected_return REAL DEFAULT 0.05,
            volatility REAL DEFAULT 0.15,
            dividend_yield REAL DEFAULT 0.02,
            expense_ratio REAL DEFAULT 0.001,
            nisa_eligible INTEGER DEFAULT 1,
            tsumitate_eligible INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS benchmarks (
            ticker TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            asset_class TEXT NOT NULL,
            region TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


def populate_sample_securities():
    """Populate database with sample securities data."""
    conn = sqlite3.connect(SECURITIES_DB_PATH)
    cursor = conn.cursor()
    
    # Sample investment trusts (eMAXIS Slim series and others)
    sample_securities = [
        # eMAXIS Slim series
        ('03311187', 'eMAXIS Slim 全世界株式（オール・カントリー）', 'foreign_stock', 'global', 'JPY', 0.08, 0.18, 0.02, 0.0005775, 1, 1),
        ('03311183', 'eMAXIS Slim 米国株式（S&P500）', 'foreign_stock', 'us', 'JPY', 0.10, 0.20, 0.015, 0.0009372, 1, 1),
        ('03311172', 'eMAXIS Slim 先進国株式インデックス', 'foreign_stock', 'developed', 'JPY', 0.07, 0.17, 0.018, 0.0009889, 1, 1),
        ('03311167', 'eMAXIS Slim 国内株式（TOPIX）', 'domestic_stock', 'japan', 'JPY', 0.05, 0.16, 0.022, 0.000143, 1, 1),
        ('03311169', 'eMAXIS Slim 新興国株式インデックス', 'foreign_stock', 'emerging', 'JPY', 0.06, 0.25, 0.025, 0.001859, 1, 1),
        ('03311175', 'eMAXIS Slim 先進国債券インデックス', 'foreign_bond', 'developed', 'JPY', 0.02, 0.06, 0.03, 0.000154, 1, 1),
        ('03311179', 'eMAXIS Slim 国内債券インデックス', 'domestic_bond', 'japan', 'JPY', 0.01, 0.03, 0.01, 0.000132, 1, 1),
        ('03311184', 'eMAXIS Slim バランス（8資産均等型）', 'balanced', 'global', 'JPY', 0.04, 0.10, 0.02, 0.000154, 1, 1),
        
        # Other popular funds
        ('89311199', '楽天・全世界株式インデックス・ファンド', 'foreign_stock', 'global', 'JPY', 0.08, 0.18, 0.02, 0.000132, 1, 1),
        ('89311179', '楽天・全米株式インデックス・ファンド', 'foreign_stock', 'us', 'JPY', 0.10, 0.20, 0.015, 0.000162, 1, 1),
        ('9C311125', 'SBI・V・S&P500インデックス・ファンド', 'foreign_stock', 'us', 'JPY', 0.10, 0.20, 0.015, 0.000938, 1, 1),
        ('9C311179', 'SBI・V・全世界株式インデックス・ファンド', 'foreign_stock', 'global', 'JPY', 0.08, 0.18, 0.02, 0.001022, 1, 1),
        
        # Domestic stocks
        ('79312124', 'ニッセイ日経225インデックスファンド', 'domestic_stock', 'japan', 'JPY', 0.05, 0.18, 0.02, 0.000275, 1, 1),
        ('0131100A', 'たわらノーロード 日経225', 'domestic_stock', 'japan', 'JPY', 0.05, 0.18, 0.02, 0.000187, 1, 1),
        
        # REITs
        ('03311181', 'eMAXIS Slim 国内リートインデックス', 'reit', 'japan', 'JPY', 0.04, 0.15, 0.035, 0.000187, 1, 0),
        ('03311182', 'eMAXIS Slim 先進国リートインデックス', 'reit', 'developed', 'JPY', 0.05, 0.18, 0.04, 0.00022, 1, 0),
        
        # Active funds (higher expense ratio)
        ('0431104C', 'ひふみプラス', 'domestic_stock', 'japan', 'JPY', 0.06, 0.20, 0.01, 0.01078, 1, 0),
        ('79311177', 'セゾン・グローバルバランスファンド', 'balanced', 'global', 'JPY', 0.04, 0.12, 0.015, 0.0056, 1, 0),
        
        # Bond funds
        ('64311081', '野村インデックスファンド・国内債券', 'domestic_bond', 'japan', 'JPY', 0.01, 0.03, 0.01, 0.00044, 1, 0),
        ('64311091', '野村インデックスファンド・外国債券', 'foreign_bond', 'developed', 'JPY', 0.02, 0.08, 0.025, 0.00055, 1, 0),
    ]
    
    # Insert securities
    cursor.executemany('''
        INSERT OR REPLACE INTO securities 
        (ticker, name, asset_class, region, currency, expected_return, volatility, 
         dividend_yield, expense_ratio, nisa_eligible, tsumitate_eligible)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_securities)
    
    # Sample benchmarks
    benchmarks = [
        ('TOPIX', 'TOPIX（東証株価指数）', 'domestic_stock', 'japan'),
        ('N225', '日経平均株価', 'domestic_stock', 'japan'),
        ('SP500', 'S&P 500', 'foreign_stock', 'us'),
        ('MSCI_WORLD', 'MSCI World Index', 'foreign_stock', 'developed'),
        ('MSCI_ACWI', 'MSCI All Country World Index', 'foreign_stock', 'global'),
        ('MSCI_EM', 'MSCI Emerging Markets Index', 'foreign_stock', 'emerging'),
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO benchmarks (ticker, name, asset_class, region)
        VALUES (?, ?, ?, ?)
    ''', benchmarks)
    
    conn.commit()
    conn.close()


def search_securities(
    query: str,
    asset_class: Optional[str] = None,
    nisa_only: bool = False,
    tsumitate_only: bool = False,
    limit: int = 20
) -> List[Dict]:
    """
    Search securities by name or ticker.
    
    Args:
        query: Search query (partial match on name or ticker)
        asset_class: Filter by asset class
        nisa_only: Only return NISA-eligible securities
        tsumitate_only: Only return tsumitate-eligible securities
        limit: Maximum number of results
        
    Returns:
        List of matching securities
    """
    if not os.path.exists(SECURITIES_DB_PATH):
        init_securities_database()
        populate_sample_securities()
    
    conn = sqlite3.connect(SECURITIES_DB_PATH)
    cursor = conn.cursor()
    
    sql = '''
        SELECT ticker, name, asset_class, region, currency, 
               expected_return, volatility, dividend_yield, expense_ratio,
               nisa_eligible, tsumitate_eligible
        FROM securities
        WHERE (ticker LIKE ? OR name LIKE ?)
    '''
    params = [f'%{query}%', f'%{query}%']
    
    if asset_class:
        sql += ' AND asset_class = ?'
        params.append(asset_class)
    
    if nisa_only:
        sql += ' AND nisa_eligible = 1'
    
    if tsumitate_only:
        sql += ' AND tsumitate_eligible = 1'
    
    sql += f' LIMIT {limit}'
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            'ticker': row[0],
            'name': row[1],
            'asset_class': row[2],
            'asset_class_name': ASSET_CLASSES.get(row[2], row[2]),
            'region': row[3],
            'region_name': REGIONS.get(row[3], row[3]),
            'currency': row[4],
            'expected_return': row[5],
            'volatility': row[6],
            'dividend_yield': row[7],
            'expense_ratio': row[8],
            'nisa_eligible': bool(row[9]),
            'tsumitate_eligible': bool(row[10]),
        })
    
    return results


def get_security_by_ticker(ticker: str) -> Optional[Dict]:
    """Get security details by ticker."""
    results = search_securities(ticker, limit=1)
    if results and results[0]['ticker'] == ticker:
        return results[0]
    return None


def get_all_securities() -> List[Dict]:
    """Get all securities in the database."""
    return search_securities('', limit=1000)


def get_securities_by_asset_class(asset_class: str) -> List[Dict]:
    """Get all securities of a specific asset class."""
    return search_securities('', asset_class=asset_class, limit=1000)


def get_benchmarks() -> List[Dict]:
    """Get all benchmark indices."""
    if not os.path.exists(SECURITIES_DB_PATH):
        init_securities_database()
        populate_sample_securities()
    
    conn = sqlite3.connect(SECURITIES_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT ticker, name, asset_class, region FROM benchmarks')
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            'ticker': row[0],
            'name': row[1],
            'asset_class': row[2],
            'region': row[3],
        }
        for row in rows
    ]


def add_custom_security(security: Dict) -> bool:
    """
    Add a custom security to the database.
    
    Args:
        security: Dictionary with security details
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(SECURITIES_DB_PATH):
        init_securities_database()
    
    required_fields = ['ticker', 'name', 'asset_class']
    for field in required_fields:
        if field not in security:
            return False
    
    conn = sqlite3.connect(SECURITIES_DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO securities 
            (ticker, name, asset_class, region, currency, expected_return, volatility,
             dividend_yield, expense_ratio, nisa_eligible, tsumitate_eligible)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            security['ticker'],
            security['name'],
            security['asset_class'],
            security.get('region', 'japan'),
            security.get('currency', 'JPY'),
            security.get('expected_return', 0.05),
            security.get('volatility', 0.15),
            security.get('dividend_yield', 0.02),
            security.get('expense_ratio', 0.001),
            1 if security.get('nisa_eligible', True) else 0,
            1 if security.get('tsumitate_eligible', False) else 0,
        ))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def calculate_portfolio_metrics(holdings: List[Dict]) -> Dict:
    """
    Calculate portfolio-level metrics from holdings.
    
    Args:
        holdings: List of holdings with 'ticker' and 'value' keys
        
    Returns:
        Dictionary with portfolio metrics
    """
    if not holdings:
        return {
            'total_value': 0,
            'expected_return': 0,
            'volatility': 0,
            'dividend_yield': 0,
            'expense_ratio': 0,
            'asset_allocation': {},
        }
    
    total_value = sum(h.get('value', 0) for h in holdings)
    if total_value == 0:
        return {
            'total_value': 0,
            'expected_return': 0,
            'volatility': 0,
            'dividend_yield': 0,
            'expense_ratio': 0,
            'asset_allocation': {},
        }
    
    weighted_return = 0
    weighted_volatility = 0
    weighted_dividend = 0
    weighted_expense = 0
    asset_allocation = {}
    
    for holding in holdings:
        ticker = holding.get('ticker')
        value = holding.get('value', 0)
        weight = value / total_value
        
        security = get_security_by_ticker(ticker)
        if security:
            weighted_return += security['expected_return'] * weight
            weighted_volatility += security['volatility'] * weight
            weighted_dividend += security['dividend_yield'] * weight
            weighted_expense += security['expense_ratio'] * weight
            
            asset_class = security['asset_class_name']
            asset_allocation[asset_class] = asset_allocation.get(asset_class, 0) + value
    
    return {
        'total_value': total_value,
        'expected_return': weighted_return,
        'volatility': weighted_volatility,
        'dividend_yield': weighted_dividend,
        'expense_ratio': weighted_expense,
        'asset_allocation': asset_allocation,
    }
