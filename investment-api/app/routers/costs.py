"""
Cost-related API routes (education, housing, vehicle, travel).
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List

from app.models.schemas import (
    EducationCostRequest,
    EducationCashflowRequest,
    EducationCostResponse,
    HousingCostRequest,
    HousingCostResponse,
    VehicleCostRequest,
    VehicleCostResponse,
    TravelCostRequest,
    TravelCostResponse,
)
from app.services.education_cost import (
    EDUCATION_PATHS,
    get_education_path_names,
    calculate_total_education_cost,
    generate_education_cashflow,
    get_education_summary,
    estimate_remaining_education_cost,
)
from app.services.housing_cost import (
    HOUSING_TYPES,
    RENOVATION_COSTS,
    suggest_renovations,
    calculate_total_housing_cost,
    get_housing_cashflow,
)
from app.services.vehicle_cost import (
    VEHICLE_TYPES,
    REPLACEMENT_CYCLES,
    get_vehicle_type_names,
    get_replacement_cycle_names,
    calculate_annual_running_cost,
    calculate_vehicle_cashflow,
    get_vehicle_summary,
)
from app.services.travel_cost import (
    TRAVEL_TYPES,
    TRAVEL_FREQUENCIES,
    get_travel_type_names,
    get_frequency_names,
    calculate_annual_travel_cost,
    calculate_total_travel_cost,
    get_travel_summary,
)

router = APIRouter(prefix="/api/costs", tags=["costs"])


# ==================== Education ====================

@router.get("/education/paths")
async def get_education_paths() -> Dict:
    """Get all available education paths."""
    paths = {}
    for path_id, path in EDUCATION_PATHS.items():
        paths[path_id] = {
            "name": path.name,
            "description": path.description,
        }
    return {"paths": paths}


@router.post("/education/calculate")
async def calculate_education_cost(request: EducationCostRequest) -> EducationCostResponse:
    """Calculate total education cost for a given path."""
    try:
        summary = get_education_summary(request.path_id, request.living_away)
        return EducationCostResponse(
            total_cost=summary["total_cost"],
            breakdown=summary["breakdown"],
            path_name=summary["name"],
            path_description=summary["description"],
            living_away=summary["living_away"],
            note=summary["note"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/education/cashflow")
async def get_education_cashflow(request: EducationCashflowRequest) -> Dict:
    """Generate year-by-year education cashflow."""
    try:
        cashflow = generate_education_cashflow(
            request.child_age,
            request.path_id,
            request.living_away,
            request.inflation_rate,
        )
        remaining_cost = estimate_remaining_education_cost(
            request.child_age,
            request.path_id,
            request.living_away,
        )
        return {
            "cashflow": cashflow,
            "remaining_cost": remaining_cost,
            "child_age": request.child_age,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Housing ====================

@router.get("/housing/types")
async def get_housing_types() -> Dict:
    """Get all available housing types."""
    return {"types": HOUSING_TYPES}


@router.get("/housing/renovations")
async def get_renovation_types() -> Dict:
    """Get all renovation types and costs."""
    return {"renovations": RENOVATION_COSTS}


@router.post("/housing/calculate")
async def calculate_housing_cost(request: HousingCostRequest) -> HousingCostResponse:
    """Calculate total housing cost."""
    try:
        result = calculate_total_housing_cost(
            request.housing_type,
            request.building_age,
            request.monthly_rent,
            request.loan_balance,
            request.loan_rate,
            request.loan_monthly_payment,
            request.loan_remaining_years,
            request.years_to_simulate,
            request.include_renovations,
        )
        return HousingCostResponse(
            rent_total=result["rent_total"],
            loan_principal_total=result["loan_principal_total"],
            loan_interest_total=result["loan_interest_total"],
            renovation_total=result["renovation_total"],
            total=result["total"],
            renovations=result.get("renovations"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/housing/cashflow")
async def get_housing_cashflow_api(request: HousingCostRequest) -> Dict:
    """Generate year-by-year housing cashflow."""
    try:
        cashflow = get_housing_cashflow(
            request.housing_type,
            request.building_age,
            request.monthly_rent,
            request.loan_balance,
            request.loan_rate,
            request.loan_monthly_payment,
            request.loan_remaining_years,
            request.years_to_simulate,
            request.include_renovations,
        )
        return {"cashflow": cashflow}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/housing/renovations/suggest")
async def suggest_housing_renovations(
    housing_type: str,
    building_age: int,
    years_to_simulate: int = 30
) -> Dict:
    """Suggest renovations based on building age."""
    try:
        suggestions = suggest_renovations(housing_type, building_age, years_to_simulate)
        return {"suggestions": suggestions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Vehicle ====================

@router.get("/vehicle/types")
async def get_vehicle_types() -> Dict:
    """Get all available vehicle types."""
    return {"types": VEHICLE_TYPES}


@router.get("/vehicle/cycles")
async def get_replacement_cycles() -> Dict:
    """Get all replacement cycle options."""
    return {"cycles": REPLACEMENT_CYCLES}


@router.post("/vehicle/calculate")
async def calculate_vehicle_cost(request: VehicleCostRequest) -> VehicleCostResponse:
    """Calculate vehicle cost summary."""
    try:
        summary = get_vehicle_summary(
            request.vehicle_type,
            request.purchase_price,
            request.replacement_cycle,
            request.annual_distance,
        )
        return VehicleCostResponse(
            vehicle_name=summary["vehicle_name"],
            purchase_price=summary["purchase_price"],
            replacement_cycle=summary["replacement_cycle"],
            annual_running_cost=summary["annual_running_cost"],
            total_per_cycle=summary["total_per_cycle"],
            annual_average_cost=summary["annual_average_cost"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/vehicle/cashflow")
async def get_vehicle_cashflow(request: VehicleCostRequest) -> Dict:
    """Generate year-by-year vehicle cashflow."""
    try:
        cashflow = calculate_vehicle_cashflow(
            request.vehicle_type,
            request.purchase_price,
            request.current_age,
            request.replacement_cycle,
            request.annual_distance,
            request.years_to_simulate,
        )
        return {"cashflow": cashflow}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Travel ====================

@router.get("/travel/types")
async def get_travel_types() -> Dict:
    """Get all available travel types."""
    return {"types": TRAVEL_TYPES}


@router.get("/travel/frequencies")
async def get_travel_frequencies() -> Dict:
    """Get all frequency options."""
    return {"frequencies": TRAVEL_FREQUENCIES}


@router.post("/travel/calculate")
async def calculate_travel_cost(request: TravelCostRequest) -> TravelCostResponse:
    """Calculate total travel cost."""
    try:
        plans = [
            {
                "travel_type": p.travel_type,
                "frequency": p.frequency,
                "budget_per_trip": p.budget_per_trip,
                "num_travelers": p.num_travelers,
            }
            for p in request.travel_plans
        ]
        result = calculate_total_travel_cost(plans, request.years_to_simulate)
        return TravelCostResponse(
            annual_total=result["annual_total"],
            total=result["total"],
            years=result["years"],
            plan_details=result["plan_details"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/travel/summary")
async def get_travel_summary_api(request: TravelCostRequest) -> Dict:
    """Get travel summary."""
    try:
        plans = [
            {
                "travel_type": p.travel_type,
                "frequency": p.frequency,
                "budget_per_trip": p.budget_per_trip,
                "num_travelers": p.num_travelers,
            }
            for p in request.travel_plans
        ]
        summary = get_travel_summary(plans)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
