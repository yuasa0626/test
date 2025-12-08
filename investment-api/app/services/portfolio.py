"""
Portfolio Analysis Service
Provides portfolio analysis calculations including correlation, metrics, and optimization.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Asset class definitions with expected returns and volatilities
ASSET_CLASSES = {
    'domestic_stock': {
        'name': '国内株式',
        'expected_return': 0.05,
        'volatility': 0.18,
    },
    'foreign_stock': {
        'name': '先進国株式',
        'expected_return': 0.07,
        'volatility': 0.20,
    },
    'emerging_stock': {
        'name': '新興国株式',
        'expected_return': 0.08,
        'volatility': 0.25,
    },
    'domestic_bond': {
        'name': '国内債券',
        'expected_return': 0.01,
        'volatility': 0.03,
    },
    'foreign_bond': {
        'name': '先進国債券',
        'expected_return': 0.03,
        'volatility': 0.08,
    },
    'reit': {
        'name': 'REIT',
        'expected_return': 0.04,
        'volatility': 0.15,
    },
    'balanced': {
        'name': 'バランス型',
        'expected_return': 0.04,
        'volatility': 0.10,
    },
}

# Correlation matrix between asset classes
CORRELATION_MATRIX = {
    'domestic_stock': {'domestic_stock': 1.0, 'foreign_stock': 0.7, 'emerging_stock': 0.6, 'domestic_bond': -0.1, 'foreign_bond': 0.1, 'reit': 0.5, 'balanced': 0.7},
    'foreign_stock': {'domestic_stock': 0.7, 'foreign_stock': 1.0, 'emerging_stock': 0.8, 'domestic_bond': -0.2, 'foreign_bond': 0.2, 'reit': 0.6, 'balanced': 0.8},
    'emerging_stock': {'domestic_stock': 0.6, 'foreign_stock': 0.8, 'emerging_stock': 1.0, 'domestic_bond': -0.1, 'foreign_bond': 0.1, 'reit': 0.5, 'balanced': 0.7},
    'domestic_bond': {'domestic_stock': -0.1, 'foreign_stock': -0.2, 'emerging_stock': -0.1, 'domestic_bond': 1.0, 'foreign_bond': 0.5, 'reit': 0.0, 'balanced': 0.2},
    'foreign_bond': {'domestic_stock': 0.1, 'foreign_stock': 0.2, 'emerging_stock': 0.1, 'domestic_bond': 0.5, 'foreign_bond': 1.0, 'reit': 0.2, 'balanced': 0.4},
    'reit': {'domestic_stock': 0.5, 'foreign_stock': 0.6, 'emerging_stock': 0.5, 'domestic_bond': 0.0, 'foreign_bond': 0.2, 'reit': 1.0, 'balanced': 0.5},
    'balanced': {'domestic_stock': 0.7, 'foreign_stock': 0.8, 'emerging_stock': 0.7, 'domestic_bond': 0.2, 'foreign_bond': 0.4, 'reit': 0.5, 'balanced': 1.0},
}

# Sample securities database
SECURITIES_DB = {
    'emaxis_slim_topix': {'name': 'eMAXIS Slim 国内株式(TOPIX)', 'asset_class': 'domestic_stock', 'expense_ratio': 0.00143},
    'emaxis_slim_sp500': {'name': 'eMAXIS Slim 米国株式(S&P500)', 'asset_class': 'foreign_stock', 'expense_ratio': 0.00093},
    'emaxis_slim_allcountry': {'name': 'eMAXIS Slim 全世界株式', 'asset_class': 'foreign_stock', 'expense_ratio': 0.00113},
    'emaxis_slim_emerging': {'name': 'eMAXIS Slim 新興国株式', 'asset_class': 'emerging_stock', 'expense_ratio': 0.00187},
    'emaxis_slim_domestic_bond': {'name': 'eMAXIS Slim 国内債券', 'asset_class': 'domestic_bond', 'expense_ratio': 0.00132},
    'emaxis_slim_foreign_bond': {'name': 'eMAXIS Slim 先進国債券', 'asset_class': 'foreign_bond', 'expense_ratio': 0.00154},
    'emaxis_slim_reit': {'name': 'eMAXIS Slim 国内リート', 'asset_class': 'reit', 'expense_ratio': 0.00187},
    'emaxis_slim_balanced': {'name': 'eMAXIS Slim バランス(8資産均等型)', 'asset_class': 'balanced', 'expense_ratio': 0.00143},
    'sbi_v_sp500': {'name': 'SBI・V・S&P500', 'asset_class': 'foreign_stock', 'expense_ratio': 0.00093},
    'rakuten_vti': {'name': '楽天・全米株式', 'asset_class': 'foreign_stock', 'expense_ratio': 0.00162},
}


def get_asset_class_for_ticker(ticker: str) -> str:
    """Get asset class for a ticker."""
    if ticker in SECURITIES_DB:
        return SECURITIES_DB[ticker]['asset_class']
    # Default to foreign_stock if unknown
    return 'foreign_stock'


def get_security_info(ticker: str) -> Optional[Dict]:
    """Get security information by ticker."""
    return SECURITIES_DB.get(ticker)


def search_securities(query: str, limit: int = 10) -> List[Dict]:
    """Search securities by name or ticker."""
    results = []
    query_lower = query.lower()
    for ticker, info in SECURITIES_DB.items():
        if query_lower in ticker.lower() or query_lower in info['name'].lower():
            results.append({
                'ticker': ticker,
                'name': info['name'],
                'asset_class': info['asset_class'],
                'expense_ratio': info['expense_ratio'],
            })
            if len(results) >= limit:
                break
    return results


def calculate_portfolio_metrics(holdings: List[Dict]) -> Dict:
    """
    Calculate portfolio metrics including expected return, volatility, and Sharpe ratio.
    
    Args:
        holdings: List of holdings with ticker, current_value, asset_class
        
    Returns:
        Dictionary with portfolio metrics
    """
    if not holdings:
        return {
            'total_value': 0,
            'expected_return': 0,
            'volatility': 0,
            'sharpe_ratio': 0,
            'asset_allocation': {},
        }
    
    total_value = sum(h.get('current_value', 0) for h in holdings)
    if total_value == 0:
        return {
            'total_value': 0,
            'expected_return': 0,
            'volatility': 0,
            'sharpe_ratio': 0,
            'asset_allocation': {},
        }
    
    # Calculate weights and asset allocation
    weights = {}
    asset_allocation = {}
    
    for h in holdings:
        ticker = h.get('ticker', '')
        value = h.get('current_value', 0)
        weight = value / total_value
        
        # Get asset class
        asset_class = h.get('asset_class') or get_asset_class_for_ticker(ticker)
        
        if asset_class not in weights:
            weights[asset_class] = 0
            asset_allocation[asset_class] = 0
        
        weights[asset_class] += weight
        asset_allocation[asset_class] += value
    
    # Calculate expected return
    expected_return = sum(
        w * ASSET_CLASSES.get(ac, {'expected_return': 0.05})['expected_return']
        for ac, w in weights.items()
    )
    
    # Calculate portfolio volatility using correlation matrix
    asset_classes = list(weights.keys())
    n = len(asset_classes)
    
    if n == 0:
        volatility = 0
    elif n == 1:
        ac = asset_classes[0]
        volatility = ASSET_CLASSES.get(ac, {'volatility': 0.15})['volatility']
    else:
        # Build covariance matrix
        cov_matrix = np.zeros((n, n))
        for i, ac1 in enumerate(asset_classes):
            for j, ac2 in enumerate(asset_classes):
                vol1 = ASSET_CLASSES.get(ac1, {'volatility': 0.15})['volatility']
                vol2 = ASSET_CLASSES.get(ac2, {'volatility': 0.15})['volatility']
                corr = CORRELATION_MATRIX.get(ac1, {}).get(ac2, 0.5)
                cov_matrix[i, j] = vol1 * vol2 * corr
        
        # Portfolio variance
        weight_array = np.array([weights[ac] for ac in asset_classes])
        portfolio_variance = weight_array @ cov_matrix @ weight_array
        volatility = np.sqrt(portfolio_variance)
    
    # Sharpe ratio (assuming risk-free rate of 0.5%)
    risk_free_rate = 0.005
    sharpe_ratio = (expected_return - risk_free_rate) / volatility if volatility > 0 else 0
    
    return {
        'total_value': total_value,
        'expected_return': round(expected_return, 4),
        'volatility': round(volatility, 4),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'asset_allocation': asset_allocation,
        'weights': {ac: round(w, 4) for ac, w in weights.items()},
    }


def calculate_correlation_matrix(holdings: List[Dict]) -> Dict[str, Dict[str, float]]:
    """
    Calculate correlation matrix for portfolio holdings.
    
    Returns:
        Dictionary of correlation values between asset classes
    """
    asset_classes = set()
    for h in holdings:
        ticker = h.get('ticker', '')
        asset_class = h.get('asset_class') or get_asset_class_for_ticker(ticker)
        asset_classes.add(asset_class)
    
    result = {}
    for ac1 in asset_classes:
        result[ac1] = {}
        for ac2 in asset_classes:
            result[ac1][ac2] = CORRELATION_MATRIX.get(ac1, {}).get(ac2, 0.5)
    
    return result


def generate_efficient_frontier(
    holdings: List[Dict],
    num_portfolios: int = 100
) -> Dict:
    """
    Generate efficient frontier data for visualization.
    
    Returns:
        Dictionary with frontier points and current portfolio position
    """
    np.random.seed(42)
    
    # Get unique asset classes from holdings
    asset_classes = list(set(
        h.get('asset_class') or get_asset_class_for_ticker(h.get('ticker', ''))
        for h in holdings
    ))
    
    if len(asset_classes) < 2:
        asset_classes = ['domestic_stock', 'foreign_stock', 'domestic_bond']
    
    n = len(asset_classes)
    
    # Generate random portfolios
    frontier_points = []
    for _ in range(num_portfolios):
        # Random weights
        weights = np.random.random(n)
        weights = weights / weights.sum()
        
        # Calculate return and volatility
        expected_return = sum(
            w * ASSET_CLASSES.get(ac, {'expected_return': 0.05})['expected_return']
            for w, ac in zip(weights, asset_classes)
        )
        
        # Build covariance matrix
        cov_matrix = np.zeros((n, n))
        for i, ac1 in enumerate(asset_classes):
            for j, ac2 in enumerate(asset_classes):
                vol1 = ASSET_CLASSES.get(ac1, {'volatility': 0.15})['volatility']
                vol2 = ASSET_CLASSES.get(ac2, {'volatility': 0.15})['volatility']
                corr = CORRELATION_MATRIX.get(ac1, {}).get(ac2, 0.5)
                cov_matrix[i, j] = vol1 * vol2 * corr
        
        portfolio_variance = weights @ cov_matrix @ weights
        volatility = np.sqrt(portfolio_variance)
        
        frontier_points.append({
            'return': round(expected_return * 100, 2),
            'volatility': round(volatility * 100, 2),
        })
    
    # Current portfolio position
    current_metrics = calculate_portfolio_metrics(holdings)
    current_position = {
        'return': round(current_metrics['expected_return'] * 100, 2),
        'volatility': round(current_metrics['volatility'] * 100, 2),
    }
    
    return {
        'frontier_points': frontier_points,
        'current_position': current_position,
        'asset_classes': asset_classes,
    }


def generate_rebalancing_recommendations(
    holdings: List[Dict],
    target_allocation: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Generate rebalancing recommendations.
    
    Args:
        holdings: Current holdings
        target_allocation: Target allocation by asset class (optional)
        
    Returns:
        Dictionary with rebalancing actions
    """
    current_metrics = calculate_portfolio_metrics(holdings)
    current_weights = current_metrics.get('weights', {})
    total_value = current_metrics.get('total_value', 0)
    
    # Default target allocation if not provided
    if target_allocation is None:
        target_allocation = {
            'domestic_stock': 0.20,
            'foreign_stock': 0.40,
            'domestic_bond': 0.20,
            'foreign_bond': 0.10,
            'reit': 0.10,
        }
    
    # Calculate differences
    actions = []
    for asset_class, target_weight in target_allocation.items():
        current_weight = current_weights.get(asset_class, 0)
        diff = target_weight - current_weight
        
        if abs(diff) > 0.01:  # Only recommend if difference > 1%
            action_type = 'buy' if diff > 0 else 'sell'
            amount = abs(diff * total_value)
            
            actions.append({
                'asset_class': asset_class,
                'asset_name': ASSET_CLASSES.get(asset_class, {}).get('name', asset_class),
                'action': action_type,
                'current_weight': round(current_weight * 100, 1),
                'target_weight': round(target_weight * 100, 1),
                'amount': int(amount),
            })
    
    # Calculate expected improvement
    # Target portfolio metrics
    target_return = sum(
        w * ASSET_CLASSES.get(ac, {'expected_return': 0.05})['expected_return']
        for ac, w in target_allocation.items()
    )
    
    return {
        'current_allocation': {ac: round(w * 100, 1) for ac, w in current_weights.items()},
        'target_allocation': {ac: round(w * 100, 1) for ac, w in target_allocation.items()},
        'actions': actions,
        'expected_improvement': {
            'current_return': round(current_metrics['expected_return'] * 100, 2),
            'target_return': round(target_return * 100, 2),
            'return_improvement': round((target_return - current_metrics['expected_return']) * 100, 2),
        },
    }


def optimize_nisa_allocation(holdings: List[Dict], annual_nisa_limit: int = 3600000) -> Dict:
    """
    Optimize NISA allocation for tax efficiency.
    
    High-return assets should be prioritized for NISA accounts.
    
    Returns:
        Dictionary with NISA optimization recommendations
    """
    # Separate holdings by account type
    nisa_holdings = [h for h in holdings if h.get('account_type', '').startswith('nisa')]
    tokutei_holdings = [h for h in holdings if h.get('account_type', '') == 'tokutei']
    
    nisa_total = sum(h.get('current_value', 0) for h in nisa_holdings)
    tokutei_total = sum(h.get('current_value', 0) for h in tokutei_holdings)
    
    # Find high-return assets in tokutei that should be in NISA
    recommended_moves = []
    
    for h in tokutei_holdings:
        ticker = h.get('ticker', '')
        asset_class = h.get('asset_class') or get_asset_class_for_ticker(ticker)
        expected_return = ASSET_CLASSES.get(asset_class, {}).get('expected_return', 0.05)
        
        # Recommend moving high-return assets (>5% expected return) to NISA
        if expected_return > 0.05:
            value = h.get('current_value', 0)
            # Estimate tax savings (20.315% on gains)
            estimated_gain = value * expected_return * 10  # 10-year projection
            tax_savings = int(estimated_gain * 0.20315)
            
            recommended_moves.append({
                'ticker': ticker,
                'name': h.get('name', ticker),
                'current_value': value,
                'expected_return': round(expected_return * 100, 2),
                'estimated_tax_savings_10y': tax_savings,
                'priority': 'high' if expected_return > 0.07 else 'medium',
            })
    
    # Sort by expected return (highest first)
    recommended_moves.sort(key=lambda x: x['expected_return'], reverse=True)
    
    # Calculate total estimated tax savings
    total_tax_savings = sum(m['estimated_tax_savings_10y'] for m in recommended_moves)
    
    return {
        'current_nisa_total': nisa_total,
        'current_tokutei_total': tokutei_total,
        'annual_nisa_limit': annual_nisa_limit,
        'recommended_moves': recommended_moves,
        'estimated_tax_savings': total_tax_savings,
        'note': '※NISA口座では運用益が非課税となるため、高リターン資産を優先的に配置することで税効率が向上します。',
    }
