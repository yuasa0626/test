"""
Shared UI components for the investment portfolio analysis tool.
Contains reusable rendering functions for charts and metrics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List

from data_fetcher import (
    get_fund_info,
    create_returns_matrix,
    FUND_DEFINITIONS
)
from analyzer import (
    analyze_portfolio,
    analyze_crisis_period,
    monte_carlo_simulation,
    calculate_correlation_matrix,
    calculate_contribution_to_risk,
    get_crisis_periods,
    PortfolioMetrics,
    TRADING_DAYS
)


def calculate_weights(portfolio: Dict[str, float]) -> Dict[str, float]:
    """Convert amounts to weights."""
    total = sum(portfolio.values())
    if total == 0:
        return {}
    return {fund_id: amount / total for fund_id, amount in portfolio.items()}


def render_portfolio_summary(portfolio: Dict[str, float], name: str):
    """Render portfolio composition summary."""
    if not portfolio:
        st.info(f"{name}にファンドが選択されていません")
        return
    
    total = sum(portfolio.values())
    weights = calculate_weights(portfolio)
    
    st.subheader(f"{name} 構成")
    st.metric("合計金額", f"¥{total:,.0f}")
    
    # Create composition table
    data = []
    for fund_id, amount in portfolio.items():
        fund_info = get_fund_info(fund_id)
        data.append({
            "ファンドID": fund_id,
            "ファンド名": fund_info['name'],
            "金額 (JPY)": f"¥{amount:,.0f}",
            "比率": f"{weights[fund_id]*100:.1f}%",
            "カテゴリ": fund_info['category']
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Pie chart
    fig = px.pie(
        values=list(portfolio.values()),
        names=[get_fund_info(fid)['name'][:20] for fid in portfolio.keys()],
        title=f"{name} 配分"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)


def render_metrics_card(metrics: PortfolioMetrics, name: str):
    """Render metrics in a card format."""
    st.subheader(f"{name} パフォーマンス指標")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "トータルリターン",
            f"{metrics.total_return*100:.2f}%"
        )
        st.metric(
            "年率リターン",
            f"{metrics.annualized_return*100:.2f}%"
        )
    
    with col2:
        st.metric(
            "ボラティリティ (年率)",
            f"{metrics.volatility*100:.2f}%"
        )
        st.metric(
            "シャープレシオ",
            f"{metrics.sharpe_ratio:.3f}"
        )
    
    with col3:
        st.metric(
            "最大ドローダウン",
            f"{metrics.max_drawdown*100:.2f}%"
        )
        st.metric(
            "カルマーレシオ",
            f"{metrics.calmar_ratio:.3f}"
        )
    
    with col4:
        st.metric(
            "VaR (95%, 日次)",
            f"{metrics.var_95*100:.2f}%"
        )
        st.metric(
            "CVaR (95%, 日次)",
            f"{metrics.cvar_95*100:.2f}%"
        )


def render_cumulative_return_chart(
    returns_data: Dict[str, pd.DataFrame],
    portfolio_weights: Dict[str, float],
    title: str
):
    """Render cumulative return chart."""
    if not returns_data or not portfolio_weights:
        return
    
    fig = go.Figure()
    
    # Individual fund returns
    for fund_id, df in returns_data.items():
        if fund_id in portfolio_weights:
            fund_name = get_fund_info(fund_id)['name'][:30]
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['cumulative_return'] * 100,
                mode='lines',
                name=f"{fund_id}: {fund_name}",
                opacity=0.5,
                line=dict(width=1)
            ))
    
    # Portfolio return
    returns_matrix = create_returns_matrix(returns_data, list(portfolio_weights.keys()))
    if not returns_matrix.empty:
        weights = calculate_weights(portfolio_weights)
        weight_array = np.array([weights.get(fid, 0) for fid in returns_matrix.columns])
        portfolio_returns = returns_matrix.values @ weight_array
        cumulative = (1 + pd.Series(portfolio_returns, index=returns_matrix.index)).cumprod() - 1
        
        fig.add_trace(go.Scatter(
            x=cumulative.index,
            y=cumulative.values * 100,
            mode='lines',
            name='ポートフォリオ',
            line=dict(color='red', width=3)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="日付",
        yaxis_title="累積リターン (%)",
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_correlation_heatmap(returns_matrix: pd.DataFrame):
    """Render correlation heatmap."""
    if returns_matrix.empty:
        return
    
    corr_matrix = returns_matrix.corr()
    
    # Get fund names for labels
    labels = [get_fund_info(fid)['name'][:15] for fid in corr_matrix.columns]
    
    fig = px.imshow(
        corr_matrix.values,
        x=labels,
        y=labels,
        color_continuous_scale='RdBu_r',
        zmin=-1,
        zmax=1,
        title="相関行列"
    )
    
    fig.update_layout(
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_monte_carlo_results(mc_result, initial_value: float):
    """Render Monte Carlo simulation results."""
    st.subheader("モンテカルロ・シミュレーション結果")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "期待最終価値",
            f"¥{mc_result.expected_value:,.0f}"
        )
    with col2:
        expected_return = (mc_result.expected_value - initial_value) / initial_value
        st.metric(
            "期待リターン",
            f"{expected_return*100:.1f}%"
        )
    with col3:
        st.metric(
            "損失確率",
            f"{mc_result.probability_of_loss*100:.1f}%"
        )
    with col4:
        st.metric(
            "VaR (95%)",
            f"{mc_result.var_95*100:.1f}%"
        )
    
    # Percentile paths chart
    fig = go.Figure()
    
    days = np.arange(len(mc_result.percentiles[50]))
    
    # Add percentile bands
    fig.add_trace(go.Scatter(
        x=days,
        y=mc_result.percentiles[95],
        mode='lines',
        name='95パーセンタイル',
        line=dict(color='green', dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=days,
        y=mc_result.percentiles[75],
        mode='lines',
        name='75パーセンタイル',
        line=dict(color='lightgreen')
    ))
    
    fig.add_trace(go.Scatter(
        x=days,
        y=mc_result.percentiles[50],
        mode='lines',
        name='中央値 (50パーセンタイル)',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=days,
        y=mc_result.percentiles[25],
        mode='lines',
        name='25パーセンタイル',
        line=dict(color='orange')
    ))
    
    fig.add_trace(go.Scatter(
        x=days,
        y=mc_result.percentiles[5],
        mode='lines',
        name='5パーセンタイル',
        line=dict(color='red', dash='dash')
    ))
    
    # Add initial value line
    fig.add_hline(y=initial_value, line_dash="dot", line_color="gray", 
                  annotation_text="初期価値")
    
    fig.update_layout(
        title="ポートフォリオ価値予測 (パーセンタイル推移)",
        xaxis_title="営業日数",
        yaxis_title="ポートフォリオ価値 (JPY)",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Histogram of final values
    fig_hist = px.histogram(
        x=mc_result.final_values,
        nbins=50,
        title="最終ポートフォリオ価値の分布",
        labels={'x': '最終価値 (JPY)', 'y': '頻度'}
    )
    
    fig_hist.add_vline(x=initial_value, line_dash="dash", line_color="red",
                       annotation_text="初期価値")
    fig_hist.add_vline(x=mc_result.expected_value, line_dash="dash", line_color="green",
                       annotation_text="期待価値")
    
    st.plotly_chart(fig_hist, use_container_width=True)


def render_crisis_analysis(
    returns_matrix: pd.DataFrame,
    weights: Dict[str, float],
    portfolio_name: str = "ポートフォリオ"
):
    """Render crisis period analysis."""
    crisis_periods = get_crisis_periods()
    crisis = crisis_periods.get('covid_crash', {})
    
    if not crisis:
        return
    
    results = analyze_crisis_period(
        returns_matrix,
        weights,
        crisis['start'],
        crisis['end']
    )
    
    st.subheader(f"危機時分析: {crisis['name']}")
    st.markdown(f"期間: {crisis['start'].strftime('%Y-%m-%d')} 〜 {crisis['end'].strftime('%Y-%m-%d')} ({results['n_days']} 営業日)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "期間リターン",
            f"{results['period_return']*100:.2f}%"
        )
        st.metric(
            "最大下落率",
            f"{results['max_decline']*100:.2f}%"
        )
    
    with col2:
        st.metric(
            "最悪の1日",
            f"{results['worst_day']*100:.2f}%"
        )
        st.metric(
            "年率ボラティリティ",
            f"{results['volatility']*100:.2f}%"
        )
    
    with col3:
        st.metric(
            "回復に必要なリターン",
            f"{results['recovery_needed']*100:.2f}%"
        )


def render_risk_contribution(
    returns_matrix: pd.DataFrame,
    portfolio: Dict[str, float],
    portfolio_name: str = "ポートフォリオ"
):
    """Render risk contribution analysis."""
    if not portfolio or returns_matrix.empty:
        return
    
    weights = calculate_weights(portfolio)
    weight_array = np.array([weights.get(fid, 0) for fid in returns_matrix.columns])
    cov_matrix = returns_matrix.cov().values * TRADING_DAYS
    
    risk_contrib = calculate_contribution_to_risk(weight_array, cov_matrix)
    
    st.subheader("リスク寄与度分析")
    
    contrib_data = []
    for i, fund_id in enumerate(returns_matrix.columns):
        if fund_id in portfolio:
            contrib_data.append({
                "ファンド": get_fund_info(fund_id)['name'][:30],
                "比率": f"{weights.get(fund_id, 0)*100:.1f}%",
                "リスク寄与度": f"{risk_contrib[i]*100:.1f}%"
            })
    
    if contrib_data:
        st.dataframe(pd.DataFrame(contrib_data), use_container_width=True, hide_index=True)


def render_full_analysis(
    processed_data: Dict[str, pd.DataFrame],
    returns_matrix: pd.DataFrame,
    portfolio: Dict[str, float],
    portfolio_name: str,
    mc_simulations: int,
    mc_horizon: int
):
    """Render full portfolio analysis including all sections."""
    if not portfolio:
        st.warning(f"{portfolio_name}にファンドが選択されていません。入力ページでファンドを選択してください。")
        return
    
    weights = calculate_weights(portfolio)
    
    # Portfolio composition
    render_portfolio_summary(portfolio, portfolio_name)
    
    st.markdown("---")
    
    # Performance metrics
    metrics, _ = analyze_portfolio(returns_matrix, weights)
    render_metrics_card(metrics, portfolio_name)
    
    st.markdown("---")
    
    # Cumulative return chart
    render_cumulative_return_chart(
        processed_data,
        portfolio,
        f"{portfolio_name} - 累積リターン"
    )
    
    st.markdown("---")
    
    # Risk analysis
    st.header("リスク分析")
    
    # Correlation matrix (only if multiple funds)
    if len(portfolio) > 1:
        fund_returns = create_returns_matrix(processed_data, list(portfolio.keys()))
        render_correlation_heatmap(fund_returns)
    
    # Crisis analysis
    render_crisis_analysis(returns_matrix, weights, portfolio_name)
    
    # Risk contribution
    if len(portfolio) > 1:
        render_risk_contribution(returns_matrix, portfolio, portfolio_name)
    
    st.markdown("---")
    
    # Monte Carlo simulation
    st.header("モンテカルロ・シミュレーション")
    
    initial_value = sum(portfolio.values())
    
    # Calculate portfolio parameters
    weight_array = np.array([weights.get(fid, 0) for fid in returns_matrix.columns])
    
    # Expected return (annualized)
    mean_returns = returns_matrix.mean() * TRADING_DAYS
    expected_return = np.dot(weight_array, mean_returns.values)
    
    # Volatility (annualized)
    cov_matrix = returns_matrix.cov().values * TRADING_DAYS
    volatility = np.sqrt(np.dot(weight_array.T, np.dot(cov_matrix, weight_array)))
    
    st.info(f"シミュレーションパラメータ: 期待リターン = {expected_return*100:.2f}%, ボラティリティ = {volatility*100:.2f}%")
    
    if st.button("モンテカルロ・シミュレーション実行", type="primary", key=f"mc_button_{portfolio_name}"):
        with st.spinner(f"{mc_simulations}回のシミュレーションを実行中..."):
            mc_result = monte_carlo_simulation(
                expected_return=expected_return,
                volatility=volatility,
                initial_value=initial_value,
                n_simulations=mc_simulations,
                n_days=mc_horizon,
                seed=42
            )
            
            render_monte_carlo_results(mc_result, initial_value)
