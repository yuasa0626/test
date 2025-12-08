"""
Travel Cost Model
Provides travel-related cost calculations for life planning.
"""

from typing import Dict, List
from dataclasses import dataclass

# Travel types with typical costs
TRAVEL_TYPES = {
    'domestic_day': {
        'name': '国内日帰り',
        'cost_range': (10000, 30000),
        'typical_cost': 20000,
        'duration_days': 1,
    },
    'domestic_short': {
        'name': '国内旅行（1〜2泊）',
        'cost_range': (30000, 100000),
        'typical_cost': 60000,
        'duration_days': 2,
    },
    'domestic_long': {
        'name': '国内旅行（3泊以上）',
        'cost_range': (80000, 200000),
        'typical_cost': 120000,
        'duration_days': 4,
    },
    'overseas_asia': {
        'name': '海外旅行（アジア）',
        'cost_range': (100000, 300000),
        'typical_cost': 180000,
        'duration_days': 5,
    },
    'overseas_hawaii': {
        'name': '海外旅行（ハワイ・グアム）',
        'cost_range': (200000, 500000),
        'typical_cost': 300000,
        'duration_days': 6,
    },
    'overseas_europe': {
        'name': '海外旅行（欧米）',
        'cost_range': (300000, 800000),
        'typical_cost': 500000,
        'duration_days': 8,
    },
    'overseas_luxury': {
        'name': '海外旅行（高級リゾート）',
        'cost_range': (500000, 1500000),
        'typical_cost': 800000,
        'duration_days': 7,
    },
}

# Travel frequency options
TRAVEL_FREQUENCIES = {
    'monthly': {'name': '毎月', 'times_per_year': 12},
    'bimonthly': {'name': '2ヶ月に1回', 'times_per_year': 6},
    'quarterly': {'name': '3ヶ月に1回', 'times_per_year': 4},
    'biannual': {'name': '半年に1回', 'times_per_year': 2},
    'annual': {'name': '年1回', 'times_per_year': 1},
    'biennial': {'name': '2年に1回', 'times_per_year': 0.5},
    'occasional': {'name': '不定期', 'times_per_year': 0.5},
}


@dataclass
class TravelPlan:
    """Represents a travel plan."""
    travel_type: str
    frequency: str
    budget_per_trip: int
    num_travelers: int


def get_travel_type_names() -> Dict[str, str]:
    """Get dictionary of travel_type_id -> display name."""
    return {ttype: info['name'] for ttype, info in TRAVEL_TYPES.items()}


def get_frequency_names() -> Dict[str, str]:
    """Get dictionary of frequency_id -> display name."""
    return {freq: info['name'] for freq, info in TRAVEL_FREQUENCIES.items()}


def calculate_annual_travel_cost(
    travel_type: str,
    frequency: str,
    budget_per_trip: int = None,
    num_travelers: int = 1
) -> Dict:
    """
    Calculate annual travel cost.
    
    Args:
        travel_type: Type of travel
        frequency: Travel frequency
        budget_per_trip: Budget per trip (uses typical if not specified)
        num_travelers: Number of travelers
        
    Returns:
        Dictionary with cost breakdown
    """
    if travel_type not in TRAVEL_TYPES:
        raise ValueError(f"Unknown travel type: {travel_type}")
    
    if frequency not in TRAVEL_FREQUENCIES:
        raise ValueError(f"Unknown frequency: {frequency}")
    
    tinfo = TRAVEL_TYPES[travel_type]
    finfo = TRAVEL_FREQUENCIES[frequency]
    
    if budget_per_trip is None:
        budget_per_trip = tinfo['typical_cost']
    
    cost_per_trip = budget_per_trip * num_travelers
    trips_per_year = finfo['times_per_year']
    annual_cost = int(cost_per_trip * trips_per_year)
    
    return {
        'travel_type': travel_type,
        'travel_name': tinfo['name'],
        'frequency': frequency,
        'frequency_name': finfo['name'],
        'budget_per_trip': budget_per_trip,
        'cost_per_trip': cost_per_trip,
        'trips_per_year': trips_per_year,
        'annual_cost': annual_cost,
        'num_travelers': num_travelers,
    }


def calculate_travel_cashflow(
    travel_plans: List[Dict],
    years_to_simulate: int
) -> List[Dict]:
    """
    Generate year-by-year travel cashflow.
    
    Args:
        travel_plans: List of travel plan dictionaries
        years_to_simulate: Number of years to project
        
    Returns:
        List of yearly travel costs
    """
    cashflow = []
    
    # Calculate total annual cost
    total_annual = 0
    for plan in travel_plans:
        cost_info = calculate_annual_travel_cost(
            plan['travel_type'],
            plan['frequency'],
            plan.get('budget_per_trip'),
            plan.get('num_travelers', 1)
        )
        total_annual += cost_info['annual_cost']
    
    for year in range(years_to_simulate + 1):
        cashflow.append({
            'year': year,
            'cost': total_annual if year > 0 else 0,
        })
    
    return cashflow


def calculate_total_travel_cost(
    travel_plans: List[Dict],
    years_to_simulate: int
) -> Dict:
    """
    Calculate total travel cost over simulation period.
    
    Args:
        travel_plans: List of travel plan dictionaries
        years_to_simulate: Number of years to project
        
    Returns:
        Dictionary with total costs and breakdown
    """
    plan_details = []
    total_annual = 0
    
    for plan in travel_plans:
        cost_info = calculate_annual_travel_cost(
            plan['travel_type'],
            plan['frequency'],
            plan.get('budget_per_trip'),
            plan.get('num_travelers', 1)
        )
        plan_details.append(cost_info)
        total_annual += cost_info['annual_cost']
    
    return {
        'annual_total': total_annual,
        'total': total_annual * years_to_simulate,
        'plan_details': plan_details,
        'years': years_to_simulate,
    }


def suggest_travel_budget(
    annual_income: int,
    family_size: int = 1
) -> Dict:
    """
    Suggest travel budget based on income.
    
    General rule: Travel budget should be 3-10% of annual income.
    
    Args:
        annual_income: Annual household income
        family_size: Number of family members
        
    Returns:
        Dictionary with budget suggestions
    """
    min_budget = int(annual_income * 0.03)
    max_budget = int(annual_income * 0.10)
    suggested_budget = int(annual_income * 0.05)
    
    # Suggest suitable travel types
    per_person_budget = suggested_budget / family_size
    suitable_types = []
    
    for ttype, tinfo in TRAVEL_TYPES.items():
        if tinfo['typical_cost'] <= per_person_budget * 2:  # Allow for 2 trips
            suitable_types.append({
                'type': ttype,
                'name': tinfo['name'],
                'typical_cost': tinfo['typical_cost'],
            })
    
    return {
        'min_budget': min_budget,
        'max_budget': max_budget,
        'suggested_budget': suggested_budget,
        'per_person_budget': int(per_person_budget),
        'suitable_types': suitable_types,
        'note': '※一般的に旅行費用は年収の3〜10%が目安とされています',
    }


def get_travel_summary(travel_plans: List[Dict]) -> Dict:
    """
    Get summary of all travel plans.
    
    Returns:
        Dictionary with travel summary
    """
    if not travel_plans:
        return {
            'num_plans': 0,
            'annual_total': 0,
            'plans': [],
        }
    
    plan_summaries = []
    total_annual = 0
    
    for plan in travel_plans:
        cost_info = calculate_annual_travel_cost(
            plan['travel_type'],
            plan['frequency'],
            plan.get('budget_per_trip'),
            plan.get('num_travelers', 1)
        )
        plan_summaries.append(cost_info)
        total_annual += cost_info['annual_cost']
    
    return {
        'num_plans': len(travel_plans),
        'annual_total': total_annual,
        'plans': plan_summaries,
    }
