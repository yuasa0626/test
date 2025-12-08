"""
Simulation-related API routes (Monte Carlo, stress test, fund depletion).
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List

from app.models.schemas import (
    MonteCarloRequest,
    MonteCarloResponse,
    FundDepletionRequest,
    FundDepletionResponse,
    StressTestRequest,
    StressTestResponse,
    PortfolioHolding,
)
from app.services.simulation import (
    run_monte_carlo_simulation,
    run_fund_depletion_simulation,
    run_stress_test,
    get_available_scenarios,
)

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.post("/monte-carlo")
async def monte_carlo_simulation(request: MonteCarloRequest) -> MonteCarloResponse:
    """Run Monte Carlo simulation for asset projection."""
    try:
        result = run_monte_carlo_simulation(
            initial_assets=request.initial_assets,
            monthly_investment=request.monthly_investment,
            expected_return=request.expected_return,
            volatility=request.volatility,
            years=request.years,
            num_simulations=request.num_simulations,
            inflation_rate=request.inflation_rate,
            retirement_age=request.retirement_age,
            current_age=request.current_age,
            annual_expense_after_retirement=request.annual_expense_after_retirement,
        )
        
        return MonteCarloResponse(
            percentiles=result["percentiles"],
            years=result["years"],
            final_values=result["final_values"],
            depletion_probability=result["depletion_probability"],
            depletion_age=result["depletion_age"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fund-depletion")
async def fund_depletion_simulation(request: FundDepletionRequest) -> FundDepletionResponse:
    """Run fund depletion simulation."""
    try:
        result = run_fund_depletion_simulation(
            initial_assets=request.initial_assets,
            monthly_investment=request.monthly_investment,
            expected_return=request.expected_return,
            current_age=request.current_age,
            retirement_age=request.retirement_age,
            annual_expense_after_retirement=request.annual_expense_after_retirement,
            years_to_simulate=request.years_to_simulate,
        )
        
        return FundDepletionResponse(
            asset_path=result["asset_path"],
            depletion_age=result["depletion_age"],
            final_assets=result["final_assets"],
            retirement_assets=result["retirement_assets"],
            warnings=result["warnings"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stress-test/scenarios")
async def get_stress_test_scenarios() -> Dict:
    """Get all available stress test scenarios."""
    return {"scenarios": get_available_scenarios()}


@router.post("/stress-test")
async def stress_test(request: StressTestRequest) -> Dict:
    """Run stress test on portfolio."""
    try:
        holdings = [
            {
                "ticker": h.ticker,
                "name": h.name,
                "current_value": h.current_value,
                "account_type": h.account_type,
            }
            for h in request.holdings
        ]
        
        result = run_stress_test(
            holdings=holdings,
            scenario=request.scenario,
            custom_impacts=request.custom_impacts,
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stress-test/compare")
async def compare_stress_scenarios(holdings: List[PortfolioHolding]) -> Dict:
    """Compare portfolio impact across all stress scenarios."""
    holdings_dict = [
        {
            "ticker": h.ticker,
            "name": h.name,
            "current_value": h.current_value,
            "account_type": h.account_type,
        }
        for h in holdings
    ]
    
    results = {}
    for scenario_id in get_available_scenarios().keys():
        try:
            result = run_stress_test(holdings_dict, scenario_id)
            results[scenario_id] = {
                "name": result["scenario_name"],
                "total_loss": result["total_loss"],
                "loss_percentage": result["loss_percentage"],
                "recovery_months": result["recovery_months"],
            }
        except Exception:
            continue
    
    return {"comparison": results}
