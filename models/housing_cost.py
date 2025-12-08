"""
Housing Cost Model
Provides housing-related cost calculations including renovation suggestions.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Housing types
HOUSING_TYPES = {
    'owned_house': '持家（戸建て）',
    'owned_apartment': '持家（マンション）',
    'rental': '賃貸',
}

# Renovation cost estimates (average costs in JPY)
RENOVATION_COSTS = {
    'roof': {
        'name': '屋根塗装・葺き替え',
        'typical_age': 15,  # Years after construction
        'interval': 15,     # Years between renovations
        'cost_range': (500000, 1500000),
        'applies_to': ['owned_house'],
    },
    'exterior_wall': {
        'name': '外壁塗装',
        'typical_age': 10,
        'interval': 10,
        'cost_range': (800000, 1500000),
        'applies_to': ['owned_house', 'owned_apartment'],
    },
    'water_heater': {
        'name': '給湯器交換',
        'typical_age': 10,
        'interval': 10,
        'cost_range': (150000, 400000),
        'applies_to': ['owned_house', 'owned_apartment'],
    },
    'bathroom': {
        'name': '浴室リフォーム',
        'typical_age': 20,
        'interval': 20,
        'cost_range': (500000, 1500000),
        'applies_to': ['owned_house', 'owned_apartment'],
    },
    'kitchen': {
        'name': 'キッチンリフォーム',
        'typical_age': 20,
        'interval': 20,
        'cost_range': (500000, 2000000),
        'applies_to': ['owned_house', 'owned_apartment'],
    },
    'toilet': {
        'name': 'トイレリフォーム',
        'typical_age': 15,
        'interval': 15,
        'cost_range': (150000, 500000),
        'applies_to': ['owned_house', 'owned_apartment'],
    },
    'flooring': {
        'name': '床張り替え',
        'typical_age': 15,
        'interval': 15,
        'cost_range': (300000, 800000),
        'applies_to': ['owned_house', 'owned_apartment'],
    },
    'air_conditioning': {
        'name': 'エアコン交換',
        'typical_age': 10,
        'interval': 10,
        'cost_range': (100000, 300000),
        'applies_to': ['owned_house', 'owned_apartment', 'rental'],
    },
}

# Loan types
LOAN_TYPES = {
    'fixed': '固定金利',
    'variable': '変動金利',
    'mixed': '固定期間選択型',
}


@dataclass
class HousingProfile:
    """Represents a housing profile."""
    housing_type: str
    building_age: int  # Years since construction
    monthly_rent: int  # For rental
    loan_balance: int  # Remaining loan balance
    loan_interest_rate: float  # Annual interest rate
    loan_monthly_payment: int
    loan_remaining_years: int
    planned_renovations: List[Dict]


def suggest_renovations(
    housing_type: str,
    building_age: int,
    years_to_simulate: int = 30
) -> List[Dict]:
    """
    Suggest renovations based on building age.
    
    Args:
        housing_type: Type of housing (owned_house, owned_apartment, rental)
        building_age: Current age of the building in years
        years_to_simulate: Number of years to project
        
    Returns:
        List of suggested renovations with timing and cost estimates
    """
    suggestions = []
    
    for reno_id, reno_info in RENOVATION_COSTS.items():
        if housing_type not in reno_info['applies_to']:
            continue
        
        typical_age = reno_info['typical_age']
        interval = reno_info['interval']
        cost_min, cost_max = reno_info['cost_range']
        avg_cost = (cost_min + cost_max) // 2
        
        # Calculate when next renovation is due
        if building_age < typical_age:
            # First renovation
            years_until = typical_age - building_age
        else:
            # Calculate based on interval
            years_since_typical = building_age - typical_age
            cycles_passed = years_since_typical // interval
            next_due_age = typical_age + (cycles_passed + 1) * interval
            years_until = next_due_age - building_age
        
        # Add all renovations within simulation period
        current_years_until = years_until
        while current_years_until <= years_to_simulate:
            suggestions.append({
                'id': reno_id,
                'name': reno_info['name'],
                'years_from_now': current_years_until,
                'cost_min': cost_min,
                'cost_max': cost_max,
                'cost_estimate': avg_cost,
                'building_age_at_renovation': building_age + current_years_until,
            })
            current_years_until += interval
    
    # Sort by years from now
    suggestions.sort(key=lambda x: x['years_from_now'])
    
    return suggestions


def calculate_loan_schedule(
    balance: int,
    annual_rate: float,
    monthly_payment: int,
    remaining_years: int
) -> List[Dict]:
    """
    Calculate loan amortization schedule.
    
    Args:
        balance: Current loan balance
        annual_rate: Annual interest rate (e.g., 0.01 for 1%)
        monthly_payment: Monthly payment amount
        remaining_years: Remaining years on loan
        
    Returns:
        List of yearly loan status
    """
    schedule = []
    current_balance = balance
    monthly_rate = annual_rate / 12
    
    for year in range(remaining_years + 1):
        if year == 0:
            schedule.append({
                'year': year,
                'balance': current_balance,
                'principal_paid': 0,
                'interest_paid': 0,
            })
            continue
        
        yearly_principal = 0
        yearly_interest = 0
        
        for month in range(12):
            if current_balance <= 0:
                break
            
            interest = current_balance * monthly_rate
            principal = min(monthly_payment - interest, current_balance)
            
            yearly_principal += principal
            yearly_interest += interest
            current_balance -= principal
        
        schedule.append({
            'year': year,
            'balance': max(0, current_balance),
            'principal_paid': int(yearly_principal),
            'interest_paid': int(yearly_interest),
        })
        
        if current_balance <= 0:
            break
    
    return schedule


def calculate_total_housing_cost(
    housing_type: str,
    building_age: int,
    monthly_rent: int,
    loan_balance: int,
    loan_rate: float,
    loan_monthly_payment: int,
    loan_remaining_years: int,
    years_to_simulate: int,
    include_renovations: bool = True
) -> Dict:
    """
    Calculate total housing cost over simulation period.
    
    Returns:
        Dictionary with cost breakdown
    """
    result = {
        'rent_total': 0,
        'loan_principal_total': 0,
        'loan_interest_total': 0,
        'renovation_total': 0,
        'yearly_costs': [],
    }
    
    # Rental costs
    if housing_type == 'rental':
        result['rent_total'] = monthly_rent * 12 * years_to_simulate
    
    # Loan costs
    if loan_balance > 0:
        schedule = calculate_loan_schedule(
            loan_balance, loan_rate, loan_monthly_payment, loan_remaining_years
        )
        for entry in schedule:
            result['loan_principal_total'] += entry['principal_paid']
            result['loan_interest_total'] += entry['interest_paid']
    
    # Renovation costs
    if include_renovations and housing_type != 'rental':
        renovations = suggest_renovations(housing_type, building_age, years_to_simulate)
        result['renovation_total'] = sum(r['cost_estimate'] for r in renovations)
        result['renovations'] = renovations
    
    result['total'] = (
        result['rent_total'] +
        result['loan_principal_total'] +
        result['loan_interest_total'] +
        result['renovation_total']
    )
    
    return result


def get_housing_cashflow(
    housing_type: str,
    building_age: int,
    monthly_rent: int,
    loan_balance: int,
    loan_rate: float,
    loan_monthly_payment: int,
    loan_remaining_years: int,
    years_to_simulate: int,
    include_renovations: bool = True
) -> List[Dict]:
    """
    Generate year-by-year housing cashflow.
    
    Returns:
        List of yearly housing costs
    """
    cashflow = []
    
    # Get loan schedule
    loan_schedule = []
    if loan_balance > 0:
        loan_schedule = calculate_loan_schedule(
            loan_balance, loan_rate, loan_monthly_payment, loan_remaining_years
        )
    
    # Get renovation schedule
    renovations = []
    if include_renovations and housing_type != 'rental':
        renovations = suggest_renovations(housing_type, building_age, years_to_simulate)
    
    # Build yearly cashflow
    for year in range(years_to_simulate + 1):
        yearly_cost = {
            'year': year,
            'rent': 0,
            'loan_payment': 0,
            'renovation': 0,
            'total': 0,
        }
        
        # Rent
        if housing_type == 'rental' and year > 0:
            yearly_cost['rent'] = monthly_rent * 12
        
        # Loan payment
        if year < len(loan_schedule) and year > 0:
            yearly_cost['loan_payment'] = (
                loan_schedule[year]['principal_paid'] +
                loan_schedule[year]['interest_paid']
            )
        
        # Renovations
        year_renovations = [r for r in renovations if r['years_from_now'] == year]
        yearly_cost['renovation'] = sum(r['cost_estimate'] for r in year_renovations)
        yearly_cost['renovation_items'] = [r['name'] for r in year_renovations]
        
        yearly_cost['total'] = (
            yearly_cost['rent'] +
            yearly_cost['loan_payment'] +
            yearly_cost['renovation']
        )
        
        cashflow.append(yearly_cost)
    
    return cashflow
