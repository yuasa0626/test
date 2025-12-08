"""
Vehicle Cost Model
Provides vehicle-related cost calculations including purchase, maintenance, and replacement cycles.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

# Vehicle types with typical costs
VEHICLE_TYPES = {
    'kei': {
        'name': '軽自動車',
        'purchase_range': (1000000, 2000000),
        'annual_tax': 10800,
        'annual_insurance': 50000,
        'annual_maintenance': 50000,
        'fuel_efficiency': 20,  # km/L
    },
    'compact': {
        'name': 'コンパクトカー',
        'purchase_range': (1500000, 3000000),
        'annual_tax': 30500,
        'annual_insurance': 60000,
        'annual_maintenance': 60000,
        'fuel_efficiency': 15,
    },
    'sedan': {
        'name': 'セダン',
        'purchase_range': (2500000, 5000000),
        'annual_tax': 39500,
        'annual_insurance': 70000,
        'annual_maintenance': 70000,
        'fuel_efficiency': 12,
    },
    'suv': {
        'name': 'SUV',
        'purchase_range': (3000000, 6000000),
        'annual_tax': 45000,
        'annual_insurance': 75000,
        'annual_maintenance': 80000,
        'fuel_efficiency': 10,
    },
    'minivan': {
        'name': 'ミニバン',
        'purchase_range': (2500000, 5000000),
        'annual_tax': 39500,
        'annual_insurance': 70000,
        'annual_maintenance': 75000,
        'fuel_efficiency': 11,
    },
    'hybrid': {
        'name': 'ハイブリッド車',
        'purchase_range': (2500000, 5500000),
        'annual_tax': 30500,
        'annual_insurance': 65000,
        'annual_maintenance': 65000,
        'fuel_efficiency': 25,
    },
    'ev': {
        'name': '電気自動車',
        'purchase_range': (3500000, 7000000),
        'annual_tax': 0,  # Tax exempt
        'annual_insurance': 70000,
        'annual_maintenance': 40000,
        'fuel_efficiency': 0,  # Uses electricity
        'annual_electricity': 36000,  # Estimated annual electricity cost
    },
    'luxury': {
        'name': '高級車',
        'purchase_range': (5000000, 15000000),
        'annual_tax': 76500,
        'annual_insurance': 100000,
        'annual_maintenance': 150000,
        'fuel_efficiency': 8,
    },
}

# Typical replacement cycles
REPLACEMENT_CYCLES = {
    'short': {'name': '5年', 'years': 5},
    'medium': {'name': '7年', 'years': 7},
    'long': {'name': '10年', 'years': 10},
    'very_long': {'name': '13年以上', 'years': 13},
}

# Fuel price (JPY per liter)
FUEL_PRICE = 170

# Annual driving distance (km)
DEFAULT_ANNUAL_DISTANCE = 10000


@dataclass
class VehicleProfile:
    """Represents a vehicle profile."""
    vehicle_type: str
    purchase_price: int
    current_age: int  # Years since purchase
    replacement_cycle: str
    annual_distance: int


def get_vehicle_type_names() -> Dict[str, str]:
    """Get dictionary of vehicle_type_id -> display name."""
    return {vtype: info['name'] for vtype, info in VEHICLE_TYPES.items()}


def get_replacement_cycle_names() -> Dict[str, str]:
    """Get dictionary of cycle_id -> display name."""
    return {cycle: info['name'] for cycle, info in REPLACEMENT_CYCLES.items()}


def calculate_annual_running_cost(
    vehicle_type: str,
    annual_distance: int = DEFAULT_ANNUAL_DISTANCE
) -> Dict:
    """
    Calculate annual running cost for a vehicle.
    
    Args:
        vehicle_type: Type of vehicle
        annual_distance: Annual driving distance in km
        
    Returns:
        Dictionary with cost breakdown
    """
    if vehicle_type not in VEHICLE_TYPES:
        raise ValueError(f"Unknown vehicle type: {vehicle_type}")
    
    vinfo = VEHICLE_TYPES[vehicle_type]
    
    # Fuel cost
    if vehicle_type == 'ev':
        fuel_cost = vinfo.get('annual_electricity', 36000)
    else:
        fuel_efficiency = vinfo['fuel_efficiency']
        if fuel_efficiency > 0:
            fuel_cost = (annual_distance / fuel_efficiency) * FUEL_PRICE
        else:
            fuel_cost = 0
    
    return {
        'tax': vinfo['annual_tax'],
        'insurance': vinfo['annual_insurance'],
        'maintenance': vinfo['annual_maintenance'],
        'fuel': int(fuel_cost),
        'total': int(
            vinfo['annual_tax'] +
            vinfo['annual_insurance'] +
            vinfo['annual_maintenance'] +
            fuel_cost
        ),
    }


def calculate_vehicle_cashflow(
    vehicle_type: str,
    purchase_price: int,
    current_age: int,
    replacement_cycle: str,
    annual_distance: int,
    years_to_simulate: int
) -> List[Dict]:
    """
    Generate year-by-year vehicle cashflow including replacements.
    
    Args:
        vehicle_type: Type of vehicle
        purchase_price: Purchase price of current vehicle
        current_age: Current age of vehicle in years
        replacement_cycle: Replacement cycle identifier
        annual_distance: Annual driving distance in km
        years_to_simulate: Number of years to project
        
    Returns:
        List of yearly vehicle costs
    """
    if vehicle_type not in VEHICLE_TYPES:
        raise ValueError(f"Unknown vehicle type: {vehicle_type}")
    
    if replacement_cycle not in REPLACEMENT_CYCLES:
        raise ValueError(f"Unknown replacement cycle: {replacement_cycle}")
    
    cycle_years = REPLACEMENT_CYCLES[replacement_cycle]['years']
    annual_cost = calculate_annual_running_cost(vehicle_type, annual_distance)
    
    cashflow = []
    vehicle_age = current_age
    
    for year in range(years_to_simulate + 1):
        yearly_cost = {
            'year': year,
            'running_cost': 0,
            'purchase_cost': 0,
            'total': 0,
            'vehicle_age': vehicle_age,
            'is_replacement_year': False,
        }
        
        if year == 0:
            cashflow.append(yearly_cost)
            continue
        
        # Running costs
        yearly_cost['running_cost'] = annual_cost['total']
        
        # Check for replacement
        if vehicle_age >= cycle_years:
            yearly_cost['purchase_cost'] = purchase_price
            yearly_cost['is_replacement_year'] = True
            vehicle_age = 0
        
        yearly_cost['total'] = yearly_cost['running_cost'] + yearly_cost['purchase_cost']
        yearly_cost['vehicle_age'] = vehicle_age
        
        cashflow.append(yearly_cost)
        vehicle_age += 1
    
    return cashflow


def calculate_total_vehicle_cost(
    vehicles: List[Dict],
    years_to_simulate: int
) -> Dict:
    """
    Calculate total vehicle cost for multiple vehicles.
    
    Args:
        vehicles: List of vehicle profiles
        years_to_simulate: Number of years to project
        
    Returns:
        Dictionary with total costs and breakdown
    """
    total_running = 0
    total_purchase = 0
    yearly_totals = [0] * (years_to_simulate + 1)
    
    for vehicle in vehicles:
        cashflow = calculate_vehicle_cashflow(
            vehicle['vehicle_type'],
            vehicle['purchase_price'],
            vehicle.get('current_age', 0),
            vehicle.get('replacement_cycle', 'medium'),
            vehicle.get('annual_distance', DEFAULT_ANNUAL_DISTANCE),
            years_to_simulate
        )
        
        for entry in cashflow:
            yearly_totals[entry['year']] += entry['total']
            total_running += entry['running_cost']
            total_purchase += entry['purchase_cost']
    
    return {
        'total_running': total_running,
        'total_purchase': total_purchase,
        'total': total_running + total_purchase,
        'yearly_totals': yearly_totals,
    }


def suggest_vehicle_budget(
    annual_income: int,
    num_vehicles: int = 1
) -> Dict:
    """
    Suggest vehicle budget based on income.
    
    General rule: Vehicle cost should be 30-50% of annual income.
    
    Args:
        annual_income: Annual household income
        num_vehicles: Number of vehicles
        
    Returns:
        Dictionary with budget suggestions
    """
    per_vehicle_budget = int(annual_income * 0.4 / num_vehicles)
    
    # Find suitable vehicle types
    suitable_types = []
    for vtype, vinfo in VEHICLE_TYPES.items():
        min_price, max_price = vinfo['purchase_range']
        if min_price <= per_vehicle_budget:
            suitable_types.append({
                'type': vtype,
                'name': vinfo['name'],
                'price_range': vinfo['purchase_range'],
                'within_budget': max_price <= per_vehicle_budget,
            })
    
    return {
        'suggested_budget_per_vehicle': per_vehicle_budget,
        'suitable_types': suitable_types,
        'note': '※一般的に車両価格は年収の30〜50%が目安とされています',
    }


def get_vehicle_summary(
    vehicle_type: str,
    purchase_price: int,
    replacement_cycle: str,
    annual_distance: int = DEFAULT_ANNUAL_DISTANCE
) -> Dict:
    """
    Get summary information for a vehicle.
    
    Returns:
        Dictionary with vehicle details and cost summary
    """
    if vehicle_type not in VEHICLE_TYPES:
        raise ValueError(f"Unknown vehicle type: {vehicle_type}")
    
    vinfo = VEHICLE_TYPES[vehicle_type]
    annual_cost = calculate_annual_running_cost(vehicle_type, annual_distance)
    cycle_years = REPLACEMENT_CYCLES[replacement_cycle]['years']
    
    # Calculate cost per cycle
    total_running_per_cycle = annual_cost['total'] * cycle_years
    total_per_cycle = total_running_per_cycle + purchase_price
    annual_average = total_per_cycle / cycle_years
    
    return {
        'vehicle_type': vehicle_type,
        'vehicle_name': vinfo['name'],
        'purchase_price': purchase_price,
        'replacement_cycle': REPLACEMENT_CYCLES[replacement_cycle]['name'],
        'annual_running_cost': annual_cost,
        'total_per_cycle': total_per_cycle,
        'annual_average_cost': int(annual_average),
    }
