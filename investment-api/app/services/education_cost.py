"""
Education Cost Model
Based on Japanese Ministry of Education (文部科学省) statistics.
Reference: 令和3年度子供の学習費調査 (2021)

Note: These are reference values and actual costs may vary.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import numpy as np

# Base year for cost data
BASE_YEAR = 2021

# Education stages with typical ages
EDUCATION_STAGES = {
    'kindergarten': {'name': '幼稚園', 'start_age': 3, 'years': 3},
    'elementary': {'name': '小学校', 'start_age': 6, 'years': 6},
    'junior_high': {'name': '中学校', 'start_age': 12, 'years': 3},
    'high_school': {'name': '高校', 'start_age': 15, 'years': 3},
    'university': {'name': '大学', 'start_age': 18, 'years': 4},
}

# Annual education costs by stage and type (in JPY)
# Source: 文部科学省「令和3年度子供の学習費調査」
EDUCATION_COSTS = {
    'kindergarten': {
        'public': 165126,      # 公立幼稚園
        'private': 308909,     # 私立幼稚園
    },
    'elementary': {
        'public': 352566,      # 公立小学校
        'private': 1666949,    # 私立小学校
    },
    'junior_high': {
        'public': 538799,      # 公立中学校
        'private': 1436353,    # 私立中学校
    },
    'high_school': {
        'public': 512971,      # 公立高校
        'private': 1054444,    # 私立高校
    },
    'university': {
        'national': 535800,    # 国立大学（授業料のみ）
        'public': 536363,      # 公立大学
        'private_arts': 930943,     # 私立大学文系
        'private_science': 1068627,  # 私立大学理系
        'private_medical': 2882894,  # 私立大学医歯薬系
    }
}

# University entrance fees (入学金)
UNIVERSITY_ENTRANCE_FEES = {
    'national': 282000,
    'public': 391305,
    'private_arts': 225651,
    'private_science': 251029,
    'private_medical': 1073083,
}

# Living expenses for university students living away from home (年間)
UNIVERSITY_LIVING_EXPENSES = {
    'at_home': 0,           # 自宅通学
    'away': 1200000,        # 下宿・一人暮らし
}


@dataclass
class EducationPath:
    """Represents an education path for a child."""
    name: str
    description: str
    stages: Dict[str, str]  # stage -> type (public/private/etc)
    living_away: bool = False  # For university


# Predefined education paths
EDUCATION_PATHS = {
    'all_public': EducationPath(
        name='オール公立',
        description='幼稚園から大学まで全て公立・国立',
        stages={
            'kindergarten': 'public',
            'elementary': 'public',
            'junior_high': 'public',
            'high_school': 'public',
            'university': 'national',
        }
    ),
    'public_to_private_univ': EducationPath(
        name='高校まで公立→私立大学文系',
        description='高校まで公立、大学は私立文系',
        stages={
            'kindergarten': 'public',
            'elementary': 'public',
            'junior_high': 'public',
            'high_school': 'public',
            'university': 'private_arts',
        }
    ),
    'public_to_private_science': EducationPath(
        name='高校まで公立→私立大学理系',
        description='高校まで公立、大学は私立理系',
        stages={
            'kindergarten': 'public',
            'elementary': 'public',
            'junior_high': 'public',
            'high_school': 'public',
            'university': 'private_science',
        }
    ),
    'private_junior_high': EducationPath(
        name='中学から私立→私立大学文系',
        description='中学から私立、大学は私立文系',
        stages={
            'kindergarten': 'public',
            'elementary': 'public',
            'junior_high': 'private',
            'high_school': 'private',
            'university': 'private_arts',
        }
    ),
    'all_private': EducationPath(
        name='オール私立（文系）',
        description='幼稚園から大学まで全て私立（大学は文系）',
        stages={
            'kindergarten': 'private',
            'elementary': 'private',
            'junior_high': 'private',
            'high_school': 'private',
            'university': 'private_arts',
        }
    ),
    'all_private_science': EducationPath(
        name='オール私立（理系）',
        description='幼稚園から大学まで全て私立（大学は理系）',
        stages={
            'kindergarten': 'private',
            'elementary': 'private',
            'junior_high': 'private',
            'high_school': 'private',
            'university': 'private_science',
        }
    ),
    'medical': EducationPath(
        name='医歯薬系',
        description='高校まで私立、大学は私立医歯薬系（6年）',
        stages={
            'kindergarten': 'public',
            'elementary': 'public',
            'junior_high': 'private',
            'high_school': 'private',
            'university': 'private_medical',
        }
    ),
}


def get_education_path_names() -> Dict[str, str]:
    """Get dictionary of path_id -> display name."""
    return {path_id: path.name for path_id, path in EDUCATION_PATHS.items()}


def calculate_total_education_cost(
    path_id: str,
    living_away: bool = False,
    inflation_rate: float = 0.01
) -> Tuple[int, Dict[str, int]]:
    """
    Calculate total education cost for a given path.
    
    Args:
        path_id: Education path identifier
        living_away: Whether child will live away from home during university
        inflation_rate: Annual inflation rate for cost adjustment
        
    Returns:
        Tuple of (total_cost, breakdown_by_stage)
    """
    if path_id not in EDUCATION_PATHS:
        raise ValueError(f"Unknown education path: {path_id}")
    
    path = EDUCATION_PATHS[path_id]
    breakdown = {}
    total = 0
    
    for stage, stage_type in path.stages.items():
        stage_info = EDUCATION_STAGES[stage]
        years = stage_info['years']
        
        # Special case for medical school (6 years)
        if stage == 'university' and stage_type == 'private_medical':
            years = 6
        
        # Get annual cost
        if stage == 'university':
            annual_cost = EDUCATION_COSTS[stage].get(stage_type, 0)
            # Add entrance fee for first year
            entrance_fee = UNIVERSITY_ENTRANCE_FEES.get(stage_type, 0)
            # Add living expenses if away from home
            if living_away:
                annual_cost += UNIVERSITY_LIVING_EXPENSES['away']
        else:
            annual_cost = EDUCATION_COSTS[stage].get(stage_type, 0)
            entrance_fee = 0
        
        stage_total = annual_cost * years + entrance_fee
        breakdown[stage_info['name']] = stage_total
        total += stage_total
    
    return total, breakdown


def generate_education_cashflow(
    child_age: int,
    path_id: str,
    living_away: bool = False,
    inflation_rate: float = 0.01
) -> List[Dict]:
    """
    Generate year-by-year education cost cashflow for a child.
    
    Args:
        child_age: Current age of the child
        path_id: Education path identifier
        living_away: Whether child will live away from home during university
        inflation_rate: Annual inflation rate
        
    Returns:
        List of dicts with 'years_from_now', 'age', 'stage', 'cost'
    """
    if path_id not in EDUCATION_PATHS:
        raise ValueError(f"Unknown education path: {path_id}")
    
    path = EDUCATION_PATHS[path_id]
    cashflow = []
    
    for stage, stage_type in path.stages.items():
        stage_info = EDUCATION_STAGES[stage]
        start_age = stage_info['start_age']
        years = stage_info['years']
        
        # Special case for medical school (6 years)
        if stage == 'university' and stage_type == 'private_medical':
            years = 6
        
        # Get annual cost
        if stage == 'university':
            annual_cost = EDUCATION_COSTS[stage].get(stage_type, 0)
            entrance_fee = UNIVERSITY_ENTRANCE_FEES.get(stage_type, 0)
            if living_away:
                annual_cost += UNIVERSITY_LIVING_EXPENSES['away']
        else:
            annual_cost = EDUCATION_COSTS[stage].get(stage_type, 0)
            entrance_fee = 0
        
        for year_in_stage in range(years):
            age_at_year = start_age + year_in_stage
            
            # Skip if child is already past this age
            if age_at_year < child_age:
                continue
            
            years_from_now = age_at_year - child_age
            
            # Apply inflation adjustment
            inflation_factor = (1 + inflation_rate) ** years_from_now
            adjusted_cost = annual_cost * inflation_factor
            
            # Add entrance fee for first year of university
            if stage == 'university' and year_in_stage == 0:
                adjusted_cost += entrance_fee * inflation_factor
            
            cashflow.append({
                'years_from_now': years_from_now,
                'age': age_at_year,
                'stage': stage_info['name'],
                'cost': int(adjusted_cost)
            })
    
    return cashflow


def get_education_summary(path_id: str, living_away: bool = False) -> Dict:
    """
    Get summary information for an education path.
    
    Args:
        path_id: Education path identifier
        living_away: Whether child will live away from home during university
        
    Returns:
        Dictionary with path details and cost summary
    """
    if path_id not in EDUCATION_PATHS:
        raise ValueError(f"Unknown education path: {path_id}")
    
    path = EDUCATION_PATHS[path_id]
    total, breakdown = calculate_total_education_cost(path_id, living_away)
    
    return {
        'name': path.name,
        'description': path.description,
        'total_cost': total,
        'breakdown': breakdown,
        'living_away': living_away,
        'note': '※文部科学省「令和3年度子供の学習費調査」を基に算出。実際の費用は異なる場合があります。'
    }


def estimate_remaining_education_cost(
    child_age: int,
    path_id: str,
    living_away: bool = False
) -> int:
    """
    Estimate remaining education cost from current age.
    
    Args:
        child_age: Current age of the child
        path_id: Education path identifier
        living_away: Whether child will live away from home during university
        
    Returns:
        Total remaining education cost
    """
    cashflow = generate_education_cashflow(child_age, path_id, living_away)
    return sum(item['cost'] for item in cashflow)
