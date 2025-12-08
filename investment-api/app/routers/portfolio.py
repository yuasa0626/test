"""
Portfolio-related API routes.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List

from app.models.schemas import (
    PortfolioHolding,
    PortfolioAnalysisRequest,
    PortfolioAnalysisResponse,
    RebalanceRequest,
    RebalanceResponse,
    NISAOptimizationRequest,
    NISAOptimizationResponse,
)
from app.services.portfolio import (
    ASSET_CLASSES,
    SECURITIES_DB,
    search_securities,
    get_security_info,
    calculate_portfolio_metrics,
    calculate_correlation_matrix,
    generate_efficient_frontier,
    generate_rebalancing_recommendations,
    optimize_nisa_allocation,
)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/asset-classes")
async def get_asset_classes() -> Dict:
    """Get all available asset classes with their characteristics."""
    return {"asset_classes": ASSET_CLASSES}


@router.get("/securities/search")
async def search_securities_api(query: str, limit: int = 10) -> Dict:
    """Search securities by name or ticker."""
    results = search_securities(query, limit)
    return {"results": results}


@router.get("/securities/{ticker}")
async def get_security(ticker: str) -> Dict:
    """Get security information by ticker."""
    info = get_security_info(ticker)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Security not found: {ticker}")
    return {"ticker": ticker, **info}


@router.get("/securities")
async def list_all_securities() -> Dict:
    """List all available securities."""
    securities = [
        {"ticker": ticker, **info}
        for ticker, info in SECURITIES_DB.items()
    ]
    return {"securities": securities}


@router.post("/analyze")
async def analyze_portfolio(request: PortfolioAnalysisRequest) -> Dict:
    """Analyze portfolio and return metrics."""
    holdings = [
        {
            "ticker": h.ticker,
            "name": h.name,
            "current_value": h.current_value,
            "purchase_value": h.purchase_value,
            "account_type": h.account_type,
            "expected_return": h.expected_return,
            "volatility": h.volatility,
        }
        for h in request.holdings
    ]
    
    metrics = calculate_portfolio_metrics(holdings)
    
    # Calculate P&L
    total_purchase = sum(h.purchase_value for h in request.holdings)
    total_current = sum(h.current_value for h in request.holdings)
    total_pnl = total_current - total_purchase
    pnl_percentage = (total_pnl / total_purchase * 100) if total_purchase > 0 else 0
    
    # Account allocation
    account_allocation = {}
    for h in request.holdings:
        account_type = h.account_type
        account_allocation[account_type] = account_allocation.get(account_type, 0) + h.current_value
    
    return {
        "total_value": metrics["total_value"],
        "total_purchase": total_purchase,
        "total_pnl": total_pnl,
        "pnl_percentage": round(pnl_percentage, 2),
        "expected_return": metrics["expected_return"],
        "volatility": metrics["volatility"],
        "sharpe_ratio": metrics["sharpe_ratio"],
        "asset_allocation": metrics["asset_allocation"],
        "weights": metrics.get("weights", {}),
        "account_allocation": account_allocation,
    }


@router.post("/correlation")
async def get_correlation(request: PortfolioAnalysisRequest) -> Dict:
    """Get correlation matrix for portfolio holdings."""
    holdings = [
        {
            "ticker": h.ticker,
            "name": h.name,
            "current_value": h.current_value,
        }
        for h in request.holdings
    ]
    
    correlation = calculate_correlation_matrix(holdings)
    
    # Add warnings for high correlations
    warnings = []
    asset_classes = list(correlation.keys())
    for i, ac1 in enumerate(asset_classes):
        for ac2 in asset_classes[i+1:]:
            corr_value = correlation[ac1].get(ac2, 0)
            if corr_value > 0.7:
                warnings.append({
                    "asset_class_1": ac1,
                    "asset_class_2": ac2,
                    "correlation": round(corr_value, 2),
                    "message": f"{ASSET_CLASSES.get(ac1, {}).get('name', ac1)}と{ASSET_CLASSES.get(ac2, {}).get('name', ac2)}の相関が高いです（{corr_value:.2f}）",
                })
    
    return {
        "correlation_matrix": correlation,
        "warnings": warnings,
    }


@router.post("/efficient-frontier")
async def get_efficient_frontier(request: PortfolioAnalysisRequest) -> Dict:
    """Generate efficient frontier data."""
    holdings = [
        {
            "ticker": h.ticker,
            "name": h.name,
            "current_value": h.current_value,
        }
        for h in request.holdings
    ]
    
    frontier = generate_efficient_frontier(holdings)
    return frontier


@router.post("/rebalance")
async def get_rebalancing_recommendations(request: RebalanceRequest) -> RebalanceResponse:
    """Get rebalancing recommendations."""
    holdings = [
        {
            "ticker": h.ticker,
            "name": h.name,
            "current_value": h.current_value,
        }
        for h in request.holdings
    ]
    
    result = generate_rebalancing_recommendations(holdings, request.target_allocation)
    
    return RebalanceResponse(
        current_allocation=result["current_allocation"],
        target_allocation=result["target_allocation"],
        actions=result["actions"],
        expected_improvement=result["expected_improvement"],
    )


@router.post("/nisa-optimization")
async def get_nisa_optimization(request: NISAOptimizationRequest) -> NISAOptimizationResponse:
    """Get NISA optimization recommendations."""
    holdings = [
        {
            "ticker": h.ticker,
            "name": h.name,
            "current_value": h.current_value,
            "account_type": h.account_type,
        }
        for h in request.holdings
    ]
    
    result = optimize_nisa_allocation(holdings, request.annual_nisa_limit)
    
    return NISAOptimizationResponse(
        current_nisa_total=result["current_nisa_total"],
        current_tokutei_total=result["current_tokutei_total"],
        recommended_moves=result["recommended_moves"],
        estimated_tax_savings=result["estimated_tax_savings"],
        note=result["note"],
    )
