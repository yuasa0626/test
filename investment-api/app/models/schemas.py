"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


# ==================== User Profile ====================

class FamilyMember(BaseModel):
    """Family member information."""
    type: str = Field(..., description="Type: spouse, child")
    age: int = Field(..., ge=0, le=120)
    name: Optional[str] = None


class Liability(BaseModel):
    """Liability/loan information."""
    type: str = Field(..., description="Type: housing, car, education, other")
    name: str
    balance: int = Field(..., ge=0)
    interest_rate: float = Field(..., ge=0, le=1)
    monthly_payment: int = Field(..., ge=0)
    remaining_months: int = Field(..., ge=0)


class UserProfile(BaseModel):
    """User profile information."""
    age: int = Field(..., ge=0, le=120)
    occupation: str = "会社員"
    annual_income: int = Field(default=5000000, ge=0)
    annual_expense: int = Field(default=3000000, ge=0)
    monthly_investment: int = Field(default=50000, ge=0)
    savings: int = Field(default=3000000, ge=0)
    emergency_fund: int = Field(default=1000000, ge=0)
    family_members: List[FamilyMember] = []
    liabilities: List[Liability] = []


# ==================== Education Cost ====================

class EducationCostRequest(BaseModel):
    """Request for education cost calculation."""
    path_id: str = Field(..., description="Education path ID")
    living_away: bool = Field(default=False, description="Living away from home during university")
    inflation_rate: float = Field(default=0.01, ge=0, le=0.2)


class EducationCashflowRequest(BaseModel):
    """Request for education cashflow generation."""
    child_age: int = Field(..., ge=0, le=22)
    path_id: str
    living_away: bool = False
    inflation_rate: float = Field(default=0.01, ge=0, le=0.2)


class EducationCostResponse(BaseModel):
    """Response for education cost calculation."""
    total_cost: int
    breakdown: Dict[str, int]
    path_name: str
    path_description: str
    living_away: bool
    note: str


# ==================== Housing Cost ====================

class HousingCostRequest(BaseModel):
    """Request for housing cost calculation."""
    housing_type: str = Field(..., description="owned_house, owned_apartment, rental")
    building_age: int = Field(default=0, ge=0)
    monthly_rent: int = Field(default=0, ge=0)
    loan_balance: int = Field(default=0, ge=0)
    loan_rate: float = Field(default=0.01, ge=0, le=0.2)
    loan_monthly_payment: int = Field(default=0, ge=0)
    loan_remaining_years: int = Field(default=0, ge=0)
    years_to_simulate: int = Field(default=30, ge=1, le=50)
    include_renovations: bool = True


class RenovationSuggestion(BaseModel):
    """Renovation suggestion."""
    id: str
    name: str
    years_from_now: int
    cost_min: int
    cost_max: int
    cost_estimate: int
    building_age_at_renovation: int


class HousingCostResponse(BaseModel):
    """Response for housing cost calculation."""
    rent_total: int
    loan_principal_total: int
    loan_interest_total: int
    renovation_total: int
    total: int
    renovations: Optional[List[RenovationSuggestion]] = None


# ==================== Vehicle Cost ====================

class VehicleCostRequest(BaseModel):
    """Request for vehicle cost calculation."""
    vehicle_type: str
    purchase_price: int = Field(..., ge=0)
    current_age: int = Field(default=0, ge=0)
    replacement_cycle: str = "medium"
    annual_distance: int = Field(default=10000, ge=0)
    years_to_simulate: int = Field(default=30, ge=1, le=50)


class VehicleCostResponse(BaseModel):
    """Response for vehicle cost calculation."""
    vehicle_name: str
    purchase_price: int
    replacement_cycle: str
    annual_running_cost: Dict[str, int]
    total_per_cycle: int
    annual_average_cost: int


# ==================== Travel Cost ====================

class TravelPlanRequest(BaseModel):
    """Travel plan request."""
    travel_type: str
    frequency: str
    budget_per_trip: Optional[int] = None
    num_travelers: int = Field(default=1, ge=1)


class TravelCostRequest(BaseModel):
    """Request for travel cost calculation."""
    travel_plans: List[TravelPlanRequest]
    years_to_simulate: int = Field(default=30, ge=1, le=50)


class TravelCostResponse(BaseModel):
    """Response for travel cost calculation."""
    annual_total: int
    total: int
    years: int
    plan_details: List[Dict]


# ==================== Portfolio ====================

class PortfolioHolding(BaseModel):
    """Portfolio holding."""
    ticker: str
    name: str
    current_value: int = Field(..., ge=0)
    purchase_value: int = Field(..., ge=0)
    account_type: str = Field(default="tokutei", description="tokutei, nisa_tsumitate, nisa_growth")
    expected_return: Optional[float] = None
    volatility: Optional[float] = None


class PortfolioAnalysisRequest(BaseModel):
    """Request for portfolio analysis."""
    holdings: List[PortfolioHolding]


class PortfolioAnalysisResponse(BaseModel):
    """Response for portfolio analysis."""
    total_value: int
    total_purchase: int
    total_pnl: int
    pnl_percentage: float
    asset_allocation: Dict[str, float]
    account_allocation: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None


# ==================== Simulation ====================

class MonteCarloRequest(BaseModel):
    """Request for Monte Carlo simulation."""
    initial_assets: int = Field(..., ge=0)
    monthly_investment: int = Field(default=0, ge=0)
    expected_return: float = Field(default=0.05, ge=-0.5, le=0.5)
    volatility: float = Field(default=0.15, ge=0, le=1)
    years: int = Field(default=30, ge=1, le=50)
    num_simulations: int = Field(default=1000, ge=100, le=10000)
    inflation_rate: float = Field(default=0.02, ge=0, le=0.2)
    retirement_age: Optional[int] = None
    current_age: Optional[int] = None
    annual_expense_after_retirement: int = Field(default=3000000, ge=0)


class MonteCarloResponse(BaseModel):
    """Response for Monte Carlo simulation."""
    percentiles: Dict[str, List[float]]  # 5%, 25%, 50%, 75%, 95%
    years: List[int]
    final_values: Dict[str, float]  # Statistics of final values
    depletion_probability: float
    depletion_age: Optional[int] = None


class FundDepletionRequest(BaseModel):
    """Request for fund depletion simulation."""
    initial_assets: int = Field(..., ge=0)
    monthly_investment: int = Field(default=0, ge=0)
    expected_return: float = Field(default=0.05)
    current_age: int = Field(..., ge=0, le=120)
    retirement_age: int = Field(default=65, ge=0, le=120)
    annual_expense_after_retirement: int = Field(default=3000000, ge=0)
    years_to_simulate: int = Field(default=40, ge=1, le=60)


class FundDepletionResponse(BaseModel):
    """Response for fund depletion simulation."""
    asset_path: List[Dict[str, float]]  # year, age, value
    depletion_age: Optional[int] = None
    final_assets: float
    retirement_assets: float
    warnings: List[str]


# ==================== Stress Test ====================

class StressTestRequest(BaseModel):
    """Request for stress test."""
    holdings: List[PortfolioHolding]
    scenario: str = Field(default="lehman", description="lehman, covid, dotcom, japan_bubble, custom")
    custom_impacts: Optional[Dict[str, float]] = None


class StressTestResponse(BaseModel):
    """Response for stress test."""
    scenario_name: str
    scenario_description: str
    total_value: int
    total_loss: int
    loss_percentage: float
    post_crisis_value: int
    recovery_months: int
    holdings_impact: List[Dict]
    recommendations: List[Dict]


# ==================== Strategy ====================

class RebalanceRequest(BaseModel):
    """Request for rebalancing recommendation."""
    holdings: List[PortfolioHolding]
    target_allocation: Optional[Dict[str, float]] = None


class RebalanceResponse(BaseModel):
    """Response for rebalancing recommendation."""
    current_allocation: Dict[str, float]
    target_allocation: Dict[str, float]
    actions: List[Dict]
    expected_improvement: Dict[str, float]


class NISAOptimizationRequest(BaseModel):
    """Request for NISA optimization."""
    holdings: List[PortfolioHolding]
    annual_nisa_limit: int = Field(default=3600000, ge=0)


class NISAOptimizationResponse(BaseModel):
    """Response for NISA optimization."""
    current_nisa_total: int
    current_tokutei_total: int
    recommended_moves: List[Dict]
    estimated_tax_savings: int
    note: str


# ==================== Dashboard ====================

class DashboardSummaryRequest(BaseModel):
    """Request for dashboard summary."""
    profile: UserProfile
    holdings: List[PortfolioHolding] = []
    retirement_age: int = Field(default=65, ge=0, le=120)
    annual_expense_after_retirement: int = Field(default=3000000, ge=0)


class DashboardSummaryResponse(BaseModel):
    """Response for dashboard summary."""
    total_assets: int
    portfolio_value: int
    savings: int
    emergency_fund: int
    portfolio_metrics: Optional[Dict] = None
    life_plan_summary: Dict
    stress_test_summary: Dict
    recommendations: List[str]


# ==================== Snapshot ====================

class Snapshot(BaseModel):
    """Snapshot of current state."""
    id: str
    name: str
    created_at: datetime
    profile: UserProfile
    holdings: List[PortfolioHolding]
    total_assets: int


class SnapshotCreateRequest(BaseModel):
    """Request to create snapshot."""
    name: str
    profile: UserProfile
    holdings: List[PortfolioHolding] = []
