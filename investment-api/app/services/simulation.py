"""
Simulation Service
Provides Monte Carlo simulation and stress testing functionality.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

# Crisis scenarios with historical impact data
CRISIS_SCENARIOS = {
    'lehman': {
        'name': 'リーマンショック（2008年）',
        'description': '2008年9月のリーマン・ブラザーズ破綻に端を発した世界金融危機',
        'period': '2008年9月〜2009年3月',
        'duration_months': 6,
        'recovery_months': 48,
        'asset_impacts': {
            'domestic_stock': -0.51,
            'foreign_stock': -0.57,
            'emerging_stock': -0.62,
            'domestic_bond': 0.02,
            'foreign_bond': -0.05,
            'reit': -0.65,
            'balanced': -0.35,
        },
    },
    'covid': {
        'name': 'コロナショック（2020年）',
        'description': '2020年2月〜3月のCOVID-19パンデミックによる急落',
        'period': '2020年2月〜2020年3月',
        'duration_months': 1,
        'recovery_months': 6,
        'asset_impacts': {
            'domestic_stock': -0.31,
            'foreign_stock': -0.34,
            'emerging_stock': -0.32,
            'domestic_bond': 0.01,
            'foreign_bond': -0.02,
            'reit': -0.35,
            'balanced': -0.20,
        },
    },
    'dotcom': {
        'name': 'ITバブル崩壊（2000年）',
        'description': '2000年3月のドットコムバブル崩壊',
        'period': '2000年3月〜2002年10月',
        'duration_months': 31,
        'recovery_months': 84,
        'asset_impacts': {
            'domestic_stock': -0.63,
            'foreign_stock': -0.49,
            'emerging_stock': -0.55,
            'domestic_bond': 0.05,
            'foreign_bond': 0.03,
            'reit': -0.20,
            'balanced': -0.30,
        },
    },
    'japan_bubble': {
        'name': '日本バブル崩壊（1990年）',
        'description': '1990年の日本バブル経済崩壊',
        'period': '1990年1月〜1992年8月',
        'duration_months': 32,
        'recovery_months': 360,  # Never fully recovered
        'asset_impacts': {
            'domestic_stock': -0.80,
            'foreign_stock': -0.20,
            'emerging_stock': -0.30,
            'domestic_bond': 0.10,
            'foreign_bond': 0.05,
            'reit': -0.70,
            'balanced': -0.40,
        },
    },
}


def run_monte_carlo_simulation(
    initial_assets: int,
    monthly_investment: int,
    expected_return: float,
    volatility: float,
    years: int,
    num_simulations: int = 1000,
    inflation_rate: float = 0.02,
    retirement_age: Optional[int] = None,
    current_age: Optional[int] = None,
    annual_expense_after_retirement: int = 0,
) -> Dict:
    """
    Run Monte Carlo simulation for asset projection.
    
    Uses Geometric Brownian Motion model.
    
    Returns:
        Dictionary with simulation results including percentiles
    """
    np.random.seed(42)
    
    months = years * 12
    monthly_return = expected_return / 12
    monthly_volatility = volatility / np.sqrt(12)
    monthly_inflation = inflation_rate / 12
    
    # Initialize paths
    paths = np.zeros((num_simulations, months + 1))
    paths[:, 0] = initial_assets
    
    # Determine retirement month
    retirement_month = None
    if retirement_age is not None and current_age is not None:
        years_to_retirement = retirement_age - current_age
        if years_to_retirement > 0:
            retirement_month = years_to_retirement * 12
    
    monthly_expense = annual_expense_after_retirement / 12
    
    # Simulate paths
    for sim in range(num_simulations):
        for month in range(1, months + 1):
            # Random return
            random_return = np.random.normal(monthly_return, monthly_volatility)
            
            # Investment growth
            paths[sim, month] = paths[sim, month - 1] * (1 + random_return)
            
            # Add monthly investment (before retirement)
            if retirement_month is None or month <= retirement_month:
                paths[sim, month] += monthly_investment
            else:
                # Withdraw expenses after retirement (inflation-adjusted)
                months_after_retirement = month - retirement_month
                inflation_factor = (1 + monthly_inflation) ** months_after_retirement
                paths[sim, month] -= monthly_expense * inflation_factor
            
            # Floor at zero
            paths[sim, month] = max(0, paths[sim, month])
    
    # Calculate percentiles at each year
    yearly_indices = [i * 12 for i in range(years + 1)]
    percentiles = {
        '5': [],
        '25': [],
        '50': [],
        '75': [],
        '95': [],
    }
    
    for idx in yearly_indices:
        values = paths[:, idx]
        percentiles['5'].append(float(np.percentile(values, 5)))
        percentiles['25'].append(float(np.percentile(values, 25)))
        percentiles['50'].append(float(np.percentile(values, 50)))
        percentiles['75'].append(float(np.percentile(values, 75)))
        percentiles['95'].append(float(np.percentile(values, 95)))
    
    # Final values statistics
    final_values = paths[:, -1]
    
    # Calculate depletion probability
    depletion_count = np.sum(final_values <= 0)
    depletion_probability = depletion_count / num_simulations
    
    # Find median depletion age
    depletion_age = None
    if depletion_probability > 0 and current_age is not None:
        for month in range(months + 1):
            depleted = np.sum(paths[:, month] <= 0)
            if depleted >= num_simulations * 0.5:
                depletion_age = current_age + month // 12
                break
    
    return {
        'percentiles': percentiles,
        'years': list(range(years + 1)),
        'final_values': {
            'mean': float(np.mean(final_values)),
            'median': float(np.median(final_values)),
            'std': float(np.std(final_values)),
            'min': float(np.min(final_values)),
            'max': float(np.max(final_values)),
            'p5': float(np.percentile(final_values, 5)),
            'p95': float(np.percentile(final_values, 95)),
        },
        'depletion_probability': round(depletion_probability, 4),
        'depletion_age': depletion_age,
        'num_simulations': num_simulations,
    }


def run_fund_depletion_simulation(
    initial_assets: int,
    monthly_investment: int,
    expected_return: float,
    current_age: int,
    retirement_age: int,
    annual_expense_after_retirement: int,
    years_to_simulate: int,
    inflation_rate: float = 0.02,
) -> Dict:
    """
    Run deterministic fund depletion simulation.
    
    Returns:
        Dictionary with asset path and depletion warnings
    """
    asset_path = []
    current_assets = initial_assets
    monthly_return = expected_return / 12
    monthly_expense = annual_expense_after_retirement / 12
    
    depletion_age = None
    warnings = []
    
    for year in range(years_to_simulate + 1):
        age = current_age + year
        
        asset_path.append({
            'year': year,
            'age': age,
            'value': int(current_assets),
            'is_retirement': age >= retirement_age,
        })
        
        if year == 0:
            continue
        
        # Monthly simulation for this year
        for month in range(12):
            # Investment growth
            current_assets *= (1 + monthly_return)
            
            # Add investment or withdraw expenses
            if age < retirement_age:
                current_assets += monthly_investment
            else:
                # Inflation-adjusted expense
                years_after_retirement = age - retirement_age
                inflation_factor = (1 + inflation_rate) ** years_after_retirement
                current_assets -= monthly_expense * inflation_factor
            
            # Check for depletion
            if current_assets <= 0 and depletion_age is None:
                depletion_age = age
                current_assets = 0
    
    # Generate warnings
    retirement_assets = next(
        (p['value'] for p in asset_path if p['age'] == retirement_age),
        None
    )
    
    if depletion_age is not None:
        warnings.append(f"警告: {depletion_age}歳で資金が枯渇する可能性があります")
    
    if retirement_assets is not None:
        years_of_expenses = retirement_assets / annual_expense_after_retirement
        if years_of_expenses < 20:
            warnings.append(f"注意: リタイア時の資産で約{int(years_of_expenses)}年分の生活費しか賄えません")
    
    final_assets = asset_path[-1]['value'] if asset_path else 0
    
    return {
        'asset_path': asset_path,
        'depletion_age': depletion_age,
        'final_assets': final_assets,
        'retirement_assets': retirement_assets or 0,
        'warnings': warnings,
    }


def run_stress_test(
    holdings: List[Dict],
    scenario: str,
    custom_impacts: Optional[Dict[str, float]] = None,
) -> Dict:
    """
    Run stress test on portfolio using historical crisis scenario.
    
    Args:
        holdings: List of portfolio holdings
        scenario: Crisis scenario ID
        custom_impacts: Custom impact percentages by asset class
        
    Returns:
        Dictionary with stress test results
    """
    from app.services.portfolio import get_asset_class_for_ticker, ASSET_CLASSES
    
    if scenario == 'custom' and custom_impacts:
        scenario_info = {
            'name': 'カスタムシナリオ',
            'description': 'ユーザー定義のストレスシナリオ',
            'period': 'カスタム',
            'duration_months': 6,
            'recovery_months': 24,
            'asset_impacts': custom_impacts,
        }
    elif scenario in CRISIS_SCENARIOS:
        scenario_info = CRISIS_SCENARIOS[scenario]
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    
    # Calculate impact on each holding
    total_value = sum(h.get('current_value', 0) for h in holdings)
    total_loss = 0
    holdings_impact = []
    
    for h in holdings:
        ticker = h.get('ticker', '')
        name = h.get('name', ticker)
        value = h.get('current_value', 0)
        asset_class = h.get('asset_class') or get_asset_class_for_ticker(ticker)
        
        # Get impact for this asset class
        impact = scenario_info['asset_impacts'].get(asset_class, -0.30)
        loss = int(value * abs(impact))
        post_crisis_value = int(value * (1 + impact))
        
        total_loss += loss
        
        holdings_impact.append({
            'ticker': ticker,
            'name': name,
            'asset_class': asset_class,
            'asset_class_name': ASSET_CLASSES.get(asset_class, {}).get('name', asset_class),
            'current_value': value,
            'impact_percentage': round(impact * 100, 1),
            'loss': loss,
            'post_crisis_value': max(0, post_crisis_value),
        })
    
    post_crisis_total = total_value - total_loss
    loss_percentage = (total_loss / total_value * 100) if total_value > 0 else 0
    
    # Generate recommendations
    recommendations = []
    
    if loss_percentage > 40:
        recommendations.append({
            'type': 'high_risk',
            'message': 'ポートフォリオのリスクが高いです。債券比率を増やすことを検討してください。',
            'priority': 'high',
        })
    
    # Check for concentration risk
    asset_class_values = {}
    for h in holdings_impact:
        ac = h['asset_class']
        asset_class_values[ac] = asset_class_values.get(ac, 0) + h['current_value']
    
    for ac, value in asset_class_values.items():
        if total_value > 0 and value / total_value > 0.5:
            recommendations.append({
                'type': 'concentration',
                'message': f'{ASSET_CLASSES.get(ac, {}).get("name", ac)}への集中度が高いです。分散投資を検討してください。',
                'priority': 'medium',
            })
    
    # Check emergency fund
    if total_loss > 0:
        recommendations.append({
            'type': 'emergency_fund',
            'message': f'最大損失額{total_loss:,}円に備え、十分な緊急予備資金を確保してください。',
            'priority': 'medium',
        })
    
    return {
        'scenario_name': scenario_info['name'],
        'scenario_description': scenario_info['description'],
        'scenario_period': scenario_info['period'],
        'total_value': total_value,
        'total_loss': total_loss,
        'loss_percentage': round(loss_percentage, 1),
        'post_crisis_value': max(0, post_crisis_total),
        'duration_months': scenario_info['duration_months'],
        'recovery_months': scenario_info['recovery_months'],
        'holdings_impact': holdings_impact,
        'recommendations': recommendations,
    }


def get_available_scenarios() -> Dict:
    """Get all available crisis scenarios."""
    return {
        scenario_id: {
            'name': info['name'],
            'description': info['description'],
            'period': info['period'],
        }
        for scenario_id, info in CRISIS_SCENARIOS.items()
    }
