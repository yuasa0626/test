"""
Analyzer module for investment trust portfolio analysis tool.
Contains portfolio analysis, crisis analysis, and Monte Carlo simulation logic.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Risk-free rate (annual, Japanese government bond yield approximation)
RISK_FREE_RATE = 0.005

# Trading days per year
TRADING_DAYS = 252

# Crisis period definition (COVID-19 crash)
CRISIS_PERIODS = {
    "covid_crash": {
        "name": "COVID-19 Crash (2020)",
        "start": datetime(2020, 2, 19),
        "end": datetime(2020, 3, 23)
    },
    "china_shock": {
        "name": "China Shock (2015)",
        "start": datetime(2015, 8, 11),
        "end": datetime(2015, 8, 26)
    }
}


@dataclass
class PortfolioMetrics:
    """Container for portfolio performance metrics."""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    var_95: float
    cvar_95: float


@dataclass
class MonteCarloResult:
    """Container for Monte Carlo simulation results."""
    simulations: np.ndarray
    final_values: np.ndarray
    percentiles: Dict[int, np.ndarray]
    expected_value: float
    probability_of_loss: float
    var_95: float
    cvar_95: float


def calculate_correlation_matrix(returns_matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate correlation matrix from returns.
    
    Args:
        returns_matrix: DataFrame with fund returns as columns
        
    Returns:
        Correlation matrix as DataFrame
    """
    return returns_matrix.corr()


def calculate_covariance_matrix(returns_matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate covariance matrix from returns.
    
    Args:
        returns_matrix: DataFrame with fund returns as columns
        
    Returns:
        Covariance matrix as DataFrame
    """
    return returns_matrix.cov()


def calculate_portfolio_return(
    weights: np.ndarray,
    expected_returns: np.ndarray
) -> float:
    """
    Calculate expected portfolio return.
    
    Args:
        weights: Array of portfolio weights
        expected_returns: Array of expected returns for each asset
        
    Returns:
        Expected portfolio return
    """
    return np.dot(weights, expected_returns)


def calculate_portfolio_risk(
    weights: np.ndarray,
    covariance_matrix: np.ndarray
) -> float:
    """
    Calculate portfolio risk (standard deviation) using covariance matrix.
    
    Portfolio variance = w' * Cov * w
    
    Args:
        weights: Array of portfolio weights
        covariance_matrix: Covariance matrix of returns
        
    Returns:
        Portfolio standard deviation (risk)
    """
    portfolio_variance = np.dot(weights.T, np.dot(covariance_matrix, weights))
    return np.sqrt(portfolio_variance)


def calculate_sharpe_ratio(
    portfolio_return: float,
    portfolio_risk: float,
    risk_free_rate: float = RISK_FREE_RATE
) -> float:
    """
    Calculate Sharpe ratio.
    
    Args:
        portfolio_return: Annualized portfolio return
        portfolio_risk: Annualized portfolio volatility
        risk_free_rate: Risk-free rate
        
    Returns:
        Sharpe ratio
    """
    if portfolio_risk == 0:
        return 0.0
    return (portfolio_return - risk_free_rate) / portfolio_risk


def calculate_max_drawdown(cumulative_returns: np.ndarray) -> float:
    """
    Calculate maximum drawdown.
    
    Args:
        cumulative_returns: Array of cumulative returns (total return index)
        
    Returns:
        Maximum drawdown as a positive percentage
    """
    if len(cumulative_returns) == 0:
        return 0.0
    
    # Calculate running maximum
    running_max = np.maximum.accumulate(cumulative_returns)
    
    # Calculate drawdown at each point
    drawdowns = (cumulative_returns - running_max) / running_max
    
    # Return maximum drawdown (as positive number)
    return abs(np.min(drawdowns))


def calculate_var(returns: np.ndarray, confidence_level: float = 0.95) -> float:
    """
    Calculate Value at Risk (VaR).
    
    Args:
        returns: Array of returns
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        
    Returns:
        VaR as a positive number representing potential loss
    """
    return abs(np.percentile(returns, (1 - confidence_level) * 100))


def calculate_cvar(returns: np.ndarray, confidence_level: float = 0.95) -> float:
    """
    Calculate Conditional Value at Risk (CVaR / Expected Shortfall).
    
    Args:
        returns: Array of returns
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        
    Returns:
        CVaR as a positive number representing expected loss beyond VaR
    """
    var = np.percentile(returns, (1 - confidence_level) * 100)
    return abs(np.mean(returns[returns <= var]))


def analyze_portfolio(
    returns_matrix: pd.DataFrame,
    weights: Dict[str, float],
    initial_value: float = 1000000
) -> Tuple[PortfolioMetrics, pd.Series]:
    """
    Comprehensive portfolio analysis.
    
    Args:
        returns_matrix: DataFrame with fund returns as columns
        weights: Dictionary mapping fund_id to weight
        initial_value: Initial portfolio value
        
    Returns:
        Tuple of (PortfolioMetrics, portfolio_returns_series)
    """
    # Ensure weights are in correct order
    fund_ids = list(returns_matrix.columns)
    weight_array = np.array([weights.get(fund_id, 0) for fund_id in fund_ids])
    
    # Normalize weights
    if weight_array.sum() > 0:
        weight_array = weight_array / weight_array.sum()
    
    # Calculate portfolio daily returns
    portfolio_returns = returns_matrix.values @ weight_array
    portfolio_returns_series = pd.Series(portfolio_returns, index=returns_matrix.index)
    
    # Calculate cumulative returns (total return index)
    cumulative_returns = (1 + portfolio_returns_series).cumprod()
    
    # Total return
    total_return = cumulative_returns.iloc[-1] - 1 if len(cumulative_returns) > 0 else 0
    
    # Annualized return
    n_days = len(portfolio_returns)
    if n_days > 0:
        annualized_return = (1 + total_return) ** (TRADING_DAYS / n_days) - 1
    else:
        annualized_return = 0
    
    # Annualized volatility
    daily_volatility = np.std(portfolio_returns)
    annualized_volatility = daily_volatility * np.sqrt(TRADING_DAYS)
    
    # Sharpe ratio
    sharpe = calculate_sharpe_ratio(annualized_return, annualized_volatility)
    
    # Maximum drawdown
    mdd = calculate_max_drawdown(cumulative_returns.values)
    
    # Calmar ratio (annualized return / max drawdown)
    calmar = annualized_return / mdd if mdd > 0 else 0
    
    # VaR and CVaR (daily)
    var_95 = calculate_var(portfolio_returns)
    cvar_95 = calculate_cvar(portfolio_returns)
    
    metrics = PortfolioMetrics(
        total_return=total_return,
        annualized_return=annualized_return,
        volatility=annualized_volatility,
        sharpe_ratio=sharpe,
        max_drawdown=mdd,
        calmar_ratio=calmar,
        var_95=var_95,
        cvar_95=cvar_95
    )
    
    return metrics, portfolio_returns_series


def analyze_crisis_period(
    returns_matrix: pd.DataFrame,
    weights: Dict[str, float],
    crisis_start: datetime,
    crisis_end: datetime
) -> Dict:
    """
    Analyze portfolio performance during a specific crisis period.
    
    Args:
        returns_matrix: DataFrame with fund returns as columns
        weights: Dictionary mapping fund_id to weight
        crisis_start: Start date of crisis period
        crisis_end: End date of crisis period
        
    Returns:
        Dictionary with crisis period analysis results
    """
    # Filter to crisis period
    mask = (returns_matrix.index >= crisis_start) & (returns_matrix.index <= crisis_end)
    crisis_returns = returns_matrix[mask]
    
    if len(crisis_returns) == 0:
        return {
            "period_return": 0,
            "max_decline": 0,
            "recovery_needed": 0,
            "worst_day": 0,
            "volatility": 0,
            "n_days": 0
        }
    
    # Calculate portfolio returns during crisis
    fund_ids = list(returns_matrix.columns)
    weight_array = np.array([weights.get(fund_id, 0) for fund_id in fund_ids])
    if weight_array.sum() > 0:
        weight_array = weight_array / weight_array.sum()
    
    portfolio_returns = crisis_returns.values @ weight_array
    
    # Cumulative return during crisis
    cumulative = (1 + pd.Series(portfolio_returns)).cumprod()
    period_return = cumulative.iloc[-1] - 1
    
    # Maximum decline during crisis
    max_decline = calculate_max_drawdown(cumulative.values)
    
    # Recovery needed to break even
    recovery_needed = 1 / (1 + period_return) - 1 if period_return < 0 else 0
    
    # Worst single day
    worst_day = np.min(portfolio_returns)
    
    # Annualized volatility during crisis
    volatility = np.std(portfolio_returns) * np.sqrt(TRADING_DAYS)
    
    return {
        "period_return": period_return,
        "max_decline": max_decline,
        "recovery_needed": recovery_needed,
        "worst_day": worst_day,
        "volatility": volatility,
        "n_days": len(crisis_returns)
    }


def monte_carlo_simulation(
    expected_return: float,
    volatility: float,
    initial_value: float,
    n_simulations: int = 5000,
    n_days: int = 252,
    seed: Optional[int] = None
) -> MonteCarloResult:
    """
    Run Monte Carlo simulation using Geometric Brownian Motion (GBM) model.
    
    GBM: dS = mu * S * dt + sigma * S * dW
    
    Discretized: S(t+dt) = S(t) * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)
    
    Args:
        expected_return: Annualized expected return (mu)
        volatility: Annualized volatility (sigma)
        initial_value: Initial portfolio value
        n_simulations: Number of simulation paths
        n_days: Number of trading days to simulate
        seed: Random seed for reproducibility
        
    Returns:
        MonteCarloResult with simulation results
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Daily parameters
    dt = 1 / TRADING_DAYS
    daily_drift = (expected_return - 0.5 * volatility ** 2) * dt
    daily_diffusion = volatility * np.sqrt(dt)
    
    # Generate random shocks (vectorized for performance)
    random_shocks = np.random.standard_normal((n_simulations, n_days))
    
    # Calculate daily returns using GBM
    daily_returns = np.exp(daily_drift + daily_diffusion * random_shocks)
    
    # Calculate price paths
    simulations = np.zeros((n_simulations, n_days + 1))
    simulations[:, 0] = initial_value
    
    for t in range(n_days):
        simulations[:, t + 1] = simulations[:, t] * daily_returns[:, t]
    
    # Final values
    final_values = simulations[:, -1]
    
    # Calculate percentiles at each time step
    percentiles = {
        5: np.percentile(simulations, 5, axis=0),
        25: np.percentile(simulations, 25, axis=0),
        50: np.percentile(simulations, 50, axis=0),
        75: np.percentile(simulations, 75, axis=0),
        95: np.percentile(simulations, 95, axis=0)
    }
    
    # Expected value
    expected_value = np.mean(final_values)
    
    # Probability of loss
    probability_of_loss = np.mean(final_values < initial_value)
    
    # VaR and CVaR on final values
    returns = (final_values - initial_value) / initial_value
    var_95 = calculate_var(returns)
    cvar_95 = calculate_cvar(returns)
    
    return MonteCarloResult(
        simulations=simulations,
        final_values=final_values,
        percentiles=percentiles,
        expected_value=expected_value,
        probability_of_loss=probability_of_loss,
        var_95=var_95,
        cvar_95=cvar_95
    )


def compare_portfolios(
    returns_matrix: pd.DataFrame,
    portfolio1_weights: Dict[str, float],
    portfolio2_weights: Dict[str, float],
    portfolio1_name: str = "Current Portfolio",
    portfolio2_name: str = "Proposed Portfolio"
) -> Dict:
    """
    Compare two portfolios.
    
    Args:
        returns_matrix: DataFrame with fund returns as columns
        portfolio1_weights: Weights for first portfolio
        portfolio2_weights: Weights for second portfolio
        portfolio1_name: Name for first portfolio
        portfolio2_name: Name for second portfolio
        
    Returns:
        Dictionary with comparison results
    """
    metrics1, returns1 = analyze_portfolio(returns_matrix, portfolio1_weights)
    metrics2, returns2 = analyze_portfolio(returns_matrix, portfolio2_weights)
    
    # Calculate correlation between portfolios
    correlation = returns1.corr(returns2)
    
    return {
        portfolio1_name: {
            "metrics": metrics1,
            "returns": returns1
        },
        portfolio2_name: {
            "metrics": metrics2,
            "returns": returns2
        },
        "correlation": correlation,
        "return_difference": metrics2.annualized_return - metrics1.annualized_return,
        "risk_difference": metrics2.volatility - metrics1.volatility,
        "sharpe_difference": metrics2.sharpe_ratio - metrics1.sharpe_ratio
    }


def calculate_diversification_ratio(
    weights: np.ndarray,
    volatilities: np.ndarray,
    covariance_matrix: np.ndarray
) -> float:
    """
    Calculate diversification ratio.
    
    DR = (sum of weighted individual volatilities) / portfolio volatility
    
    A higher ratio indicates better diversification.
    
    Args:
        weights: Array of portfolio weights
        volatilities: Array of individual asset volatilities
        covariance_matrix: Covariance matrix
        
    Returns:
        Diversification ratio
    """
    weighted_vol_sum = np.dot(weights, volatilities)
    portfolio_vol = calculate_portfolio_risk(weights, covariance_matrix)
    
    if portfolio_vol == 0:
        return 1.0
    
    return weighted_vol_sum / portfolio_vol


def calculate_contribution_to_risk(
    weights: np.ndarray,
    covariance_matrix: np.ndarray
) -> np.ndarray:
    """
    Calculate each asset's contribution to portfolio risk.
    
    Args:
        weights: Array of portfolio weights
        covariance_matrix: Covariance matrix
        
    Returns:
        Array of risk contributions (sums to 1)
    """
    portfolio_vol = calculate_portfolio_risk(weights, covariance_matrix)
    
    if portfolio_vol == 0:
        return weights
    
    # Marginal contribution to risk
    mcr = np.dot(covariance_matrix, weights) / portfolio_vol
    
    # Total contribution to risk
    tcr = weights * mcr
    
    # Percentage contribution
    return tcr / portfolio_vol


def get_crisis_periods() -> Dict:
    """Get all defined crisis periods."""
    return CRISIS_PERIODS


def calculate_rolling_metrics(
    portfolio_returns: pd.Series,
    window: int = 252
) -> pd.DataFrame:
    """
    Calculate rolling performance metrics.
    
    Args:
        portfolio_returns: Series of portfolio returns
        window: Rolling window size in days
        
    Returns:
        DataFrame with rolling metrics
    """
    rolling_return = portfolio_returns.rolling(window=window).apply(
        lambda x: (1 + x).prod() - 1
    )
    
    rolling_vol = portfolio_returns.rolling(window=window).std() * np.sqrt(TRADING_DAYS)
    
    rolling_sharpe = (rolling_return - RISK_FREE_RATE) / rolling_vol
    
    return pd.DataFrame({
        'rolling_return': rolling_return,
        'rolling_volatility': rolling_vol,
        'rolling_sharpe': rolling_sharpe
    })
