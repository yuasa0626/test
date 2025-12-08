"""
Current Analysis Dashboard Page
Provides comprehensive portfolio analysis including:
- Current portfolio input with account types (NISA/特定口座)
- Correlation heatmap with warnings
- Backtest chart vs benchmarks
- Efficient frontier analysis
- Fund depletion simulation with warnings
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.formatters import format_jpy_plain, format_jpy_jpunit, format_jpy_axis, get_axis_tickvals_ticktext
from models.securities_master import (
    search_securities, get_security_by_ticker, get_all_securities,
    ASSET_CLASSES, ACCOUNT_TYPES, calculate_portfolio_metrics,
    init_securities_database, populate_sample_securities
)
from analyzer import (
    calculate_correlation_matrix, calculate_portfolio_risk,
    calculate_sharpe_ratio, calculate_max_drawdown
)
from data_fetcher import fetch_fund_data, FUND_DEFINITIONS

# Page configuration
st.set_page_config(
    page_title="現状分析ダッシュボード",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS to hide number input spinners
st.markdown("""
<style>
/* Hide Streamlit's custom +/- buttons on number inputs */
button[data-testid="stNumberInputStepUp"],
button[data-testid="stNumberInputStepDown"] {
    display: none !important;
}

/* Also hide the button container */
div[data-testid="stNumberInput"] > div > div > div:last-child {
    display: none !important;
}

/* Chrome, Safari, Edge, Opera - hide native spinners */
input[type=number]::-webkit-outer-spin-button,
input[type=number]::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
}

/* Firefox - hide native spinners */
input[type=number] {
    -moz-appearance: textfield;
}
</style>
""", unsafe_allow_html=True)


def initialize_dashboard_session_state():
    """Initialize session state for dashboard."""
    if 'current_portfolio' not in st.session_state:
        st.session_state.current_portfolio = []
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {
            'personal': {'age': 30, 'occupation': '会社員'},
            'family': {'has_spouse': False, 'spouse_age': None, 'children': []},
            'cashflow': {'annual_income': 5000000, 'annual_expense': 3000000, 'monthly_investment': 50000},
            'assets': {'savings': 3000000, 'emergency_fund': 1000000},
            'liabilities': []
        }
    if 'retirement_plan' not in st.session_state:
        st.session_state.retirement_plan = {
            'target_age': 65,
            'annual_expense': 3000000,
            'continue_investing': True
        }
    
    # Initialize securities database
    try:
        init_securities_database()
        populate_sample_securities()
    except Exception:
        pass


def render_portfolio_input():
    """Render current portfolio input form."""
    st.markdown("### 現在のポートフォリオ")
    st.markdown("保有している金融商品を登録してください")
    
    # Get available securities
    all_securities = get_all_securities()
    security_options = {s['ticker']: f"{s['name']} ({s['ticker']})" for s in all_securities}
    
    # Also add fund definitions from data_fetcher
    for fund_id, fund_info in FUND_DEFINITIONS.items():
        if fund_id not in security_options:
            security_options[fund_id] = f"{fund_info['name']} ({fund_id})"
    
    account_type_options = list(ACCOUNT_TYPES.keys())
    
    num_holdings = st.number_input(
        "保有銘柄数",
        min_value=0,
        max_value=20,
        value=max(len(st.session_state.current_portfolio), 1),
        step=1,
        key="num_holdings"
    )
    
    holdings = []
    
    if num_holdings > 0:
        for i in range(num_holdings):
            with st.expander(f"銘柄{i+1}", expanded=i < 3):
                default_holding = st.session_state.current_portfolio[i] if i < len(st.session_state.current_portfolio) else {
                    'ticker': list(security_options.keys())[0] if security_options else '',
                    'name': '',
                    'account_type': 'tokutei',
                    'purchase_value': 1000000,
                    'current_value': 1000000,
                    'quantity': 1
                }
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Security selection
                    ticker_list = list(security_options.keys())
                    default_index = ticker_list.index(default_holding['ticker']) if default_holding['ticker'] in ticker_list else 0
                    
                    ticker = st.selectbox(
                        "銘柄",
                        options=ticker_list,
                        format_func=lambda x: security_options.get(x, x),
                        index=default_index,
                        key=f"holding_ticker_{i}"
                    )
                
                with col2:
                    account_type = st.selectbox(
                        "口座区分",
                        options=account_type_options,
                        format_func=lambda x: ACCOUNT_TYPES.get(x, x),
                        index=account_type_options.index(default_holding['account_type']) if default_holding['account_type'] in account_type_options else 0,
                        key=f"holding_account_{i}"
                    )
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    purchase_value = st.number_input(
                        "取得金額（円）",
                        min_value=0,
                        value=default_holding.get('purchase_value', 1000000),
                        step=100000,
                        format="%d",
                        key=f"holding_purchase_{i}"
                    )
                
                with col2:
                    current_value = st.number_input(
                        "現在評価額（円）",
                        min_value=0,
                        value=default_holding.get('current_value', 1000000),
                        step=100000,
                        format="%d",
                        key=f"holding_current_{i}"
                    )
                
                with col3:
                    # Calculate P&L
                    pnl = current_value - purchase_value
                    pnl_pct = (pnl / purchase_value * 100) if purchase_value > 0 else 0
                    st.metric(
                        "損益",
                        format_jpy_jpunit(pnl),
                        f"{pnl_pct:+.1f}%"
                    )
                
                # Get security info
                security_info = get_security_by_ticker(ticker)
                if security_info:
                    st.caption(f"資産クラス: {security_info['asset_class_name']} | 地域: {security_info['region_name']}")
                
                holdings.append({
                    'ticker': ticker,
                    'name': security_options.get(ticker, ticker),
                    'account_type': account_type,
                    'purchase_value': purchase_value,
                    'current_value': current_value,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
    
    return holdings


def render_portfolio_summary(holdings: List[Dict]):
    """Render portfolio summary."""
    if not holdings:
        st.info("ポートフォリオが登録されていません")
        return
    
    st.markdown("### ポートフォリオサマリー")
    
    total_purchase = sum(h['purchase_value'] for h in holdings)
    total_current = sum(h['current_value'] for h in holdings)
    total_pnl = total_current - total_purchase
    total_pnl_pct = (total_pnl / total_purchase * 100) if total_purchase > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("取得金額合計", format_jpy_jpunit(total_purchase))
    
    with col2:
        st.metric("現在評価額合計", format_jpy_jpunit(total_current))
    
    with col3:
        st.metric("損益合計", format_jpy_jpunit(total_pnl), f"{total_pnl_pct:+.1f}%")
    
    with col4:
        st.metric("保有銘柄数", f"{len(holdings)}銘柄")
    
    # Asset allocation by account type
    st.markdown("#### 口座別配分")
    account_allocation = {}
    for h in holdings:
        account_name = ACCOUNT_TYPES.get(h['account_type'], h['account_type'])
        account_allocation[account_name] = account_allocation.get(account_name, 0) + h['current_value']
    
    col1, col2 = st.columns(2)
    
    with col1:
        import plotly.express as px
        if account_allocation:
            fig = px.pie(
                values=list(account_allocation.values()),
                names=list(account_allocation.keys()),
                title="口座別配分"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Asset class allocation
        asset_allocation = {}
        for h in holdings:
            security = get_security_by_ticker(h['ticker'])
            if security:
                asset_class = security['asset_class_name']
            else:
                # Try to get from FUND_DEFINITIONS
                fund_info = FUND_DEFINITIONS.get(h['ticker'], {})
                asset_class = fund_info.get('asset_class', '不明')
            asset_allocation[asset_class] = asset_allocation.get(asset_class, 0) + h['current_value']
        
        if asset_allocation:
            fig = px.pie(
                values=list(asset_allocation.values()),
                names=list(asset_allocation.keys()),
                title="資産クラス別配分"
            )
            st.plotly_chart(fig, use_container_width=True)


def render_correlation_heatmap(holdings: List[Dict]):
    """Render correlation heatmap with warnings for high correlations."""
    if len(holdings) < 2:
        st.info("相関分析には2銘柄以上が必要です")
        return
    
    st.markdown("### 相関ヒートマップ")
    st.markdown("銘柄間の相関係数を表示します。高い相関（0.7以上）は分散効果が低いことを示します。")
    
    import plotly.figure_factory as ff
    import plotly.graph_objects as go
    
    # Get fund data for correlation calculation
    tickers = [h['ticker'] for h in holdings]
    
    # Generate simulated returns for correlation
    np.random.seed(42)
    n_days = 252
    
    returns_data = {}
    for ticker in tickers:
        # Get expected return and volatility from security info or fund definitions
        security = get_security_by_ticker(ticker)
        if security:
            exp_return = security['expected_return']
            volatility = security['volatility']
        else:
            fund_info = FUND_DEFINITIONS.get(ticker, {})
            exp_return = fund_info.get('base_return', 0.05)
            volatility = fund_info.get('volatility', 0.15)
        
        # Generate correlated returns (simplified)
        daily_return = exp_return / 252
        daily_vol = volatility / np.sqrt(252)
        returns_data[ticker] = np.random.normal(daily_return, daily_vol, n_days)
    
    # Calculate correlation matrix
    returns_df = pd.DataFrame(returns_data)
    corr_matrix = returns_df.corr()
    
    # Get display names
    display_names = []
    for ticker in tickers:
        security = get_security_by_ticker(ticker)
        if security:
            name = security['name'][:15]  # Truncate long names
        else:
            fund_info = FUND_DEFINITIONS.get(ticker, {})
            name = fund_info.get('name', ticker)[:15]
        display_names.append(name)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=display_names,
        y=display_names,
        colorscale='RdBu_r',
        zmin=-1,
        zmax=1,
        text=np.round(corr_matrix.values, 2),
        texttemplate='%{text}',
        textfont={"size": 10},
        hovertemplate='%{x} vs %{y}<br>相関係数: %{z:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="銘柄間相関係数",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Warnings for high correlations
    high_corr_pairs = []
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            corr = corr_matrix.iloc[i, j]
            if abs(corr) >= 0.7:
                high_corr_pairs.append({
                    'pair': f"{display_names[i]} - {display_names[j]}",
                    'correlation': corr
                })
    
    if high_corr_pairs:
        st.warning("高相関ペアが検出されました（分散効果が低い可能性）")
        for pair in high_corr_pairs:
            st.markdown(f"- **{pair['pair']}**: 相関係数 {pair['correlation']:.2f}")
    else:
        st.success("適切に分散されたポートフォリオです")


def render_backtest_chart(holdings: List[Dict]):
    """Render backtest chart comparing portfolio vs benchmarks."""
    if not holdings:
        st.info("バックテストにはポートフォリオが必要です")
        return
    
    st.markdown("### バックテスト（過去5年シミュレーション）")
    st.markdown("ポートフォリオの過去パフォーマンスをベンチマークと比較します")
    
    import plotly.graph_objects as go
    
    # Generate simulated historical data
    np.random.seed(42)
    n_years = 5
    n_days = n_years * 252
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='B')
    
    # Calculate portfolio weights
    total_value = sum(h['current_value'] for h in holdings)
    weights = {h['ticker']: h['current_value'] / total_value for h in holdings}
    
    # Generate portfolio returns
    portfolio_returns = np.zeros(n_days)
    
    for ticker, weight in weights.items():
        security = get_security_by_ticker(ticker)
        if security:
            exp_return = security['expected_return']
            volatility = security['volatility']
        else:
            fund_info = FUND_DEFINITIONS.get(ticker, {})
            exp_return = fund_info.get('base_return', 0.05)
            volatility = fund_info.get('volatility', 0.15)
        
        daily_return = exp_return / 252
        daily_vol = volatility / np.sqrt(252)
        asset_returns = np.random.normal(daily_return, daily_vol, n_days)
        portfolio_returns += weight * asset_returns
    
    # Calculate cumulative returns
    portfolio_cumulative = (1 + portfolio_returns).cumprod()
    
    # Generate benchmark returns (TOPIX and MSCI World)
    topix_returns = np.random.normal(0.05 / 252, 0.18 / np.sqrt(252), n_days)
    topix_cumulative = (1 + topix_returns).cumprod()
    
    msci_returns = np.random.normal(0.08 / 252, 0.16 / np.sqrt(252), n_days)
    msci_cumulative = (1 + msci_returns).cumprod()
    
    # Create chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=portfolio_cumulative * 100,
        mode='lines',
        name='ポートフォリオ',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=topix_cumulative * 100,
        mode='lines',
        name='TOPIX',
        line=dict(color='red', width=1, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=msci_cumulative * 100,
        mode='lines',
        name='MSCI World',
        line=dict(color='green', width=1, dash='dash')
    ))
    
    fig.update_layout(
        title="累積リターン比較（5年間）",
        xaxis_title="日付",
        yaxis_title="累積リターン（%）",
        height=400,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    portfolio_total_return = (portfolio_cumulative[-1] - 1) * 100
    portfolio_annual_return = ((portfolio_cumulative[-1]) ** (1/n_years) - 1) * 100
    portfolio_vol = np.std(portfolio_returns) * np.sqrt(252) * 100
    portfolio_sharpe = (portfolio_annual_return - 0.5) / portfolio_vol if portfolio_vol > 0 else 0
    
    # Calculate max drawdown
    peak = np.maximum.accumulate(portfolio_cumulative)
    drawdown = (portfolio_cumulative - peak) / peak
    max_dd = np.min(drawdown) * 100
    
    with col1:
        st.metric("累積リターン", f"{portfolio_total_return:.1f}%")
    
    with col2:
        st.metric("年率リターン", f"{portfolio_annual_return:.1f}%")
    
    with col3:
        st.metric("年率ボラティリティ", f"{portfolio_vol:.1f}%")
    
    with col4:
        st.metric("シャープレシオ", f"{portfolio_sharpe:.2f}")
    
    st.metric("最大ドローダウン", f"{max_dd:.1f}%")


def render_efficient_frontier(holdings: List[Dict]):
    """Render efficient frontier analysis."""
    st.markdown("### 効率的フロンティア分析")
    st.markdown("現在のポートフォリオがリスク・リターン平面上でどの位置にあるかを表示します")
    
    import plotly.graph_objects as go
    
    # Get available securities for frontier calculation
    all_securities = get_all_securities()
    if len(all_securities) < 3:
        # Use fund definitions if not enough securities
        for fund_id, fund_info in FUND_DEFINITIONS.items():
            all_securities.append({
                'ticker': fund_id,
                'name': fund_info['name'],
                'expected_return': fund_info['base_return'],
                'volatility': fund_info['volatility']
            })
    
    # Generate efficient frontier points
    np.random.seed(42)
    n_portfolios = 1000
    
    # Use a subset of securities for frontier
    frontier_securities = all_securities[:8]
    n_assets = len(frontier_securities)
    
    returns = np.array([s['expected_return'] for s in frontier_securities])
    volatilities = np.array([s['volatility'] for s in frontier_securities])
    
    # Generate random portfolios
    portfolio_returns = []
    portfolio_volatilities = []
    portfolio_sharpes = []
    
    for _ in range(n_portfolios):
        weights = np.random.random(n_assets)
        weights /= weights.sum()
        
        port_return = np.dot(weights, returns)
        # Simplified volatility calculation (assuming low correlation)
        port_vol = np.sqrt(np.dot(weights ** 2, volatilities ** 2))
        
        portfolio_returns.append(port_return * 100)
        portfolio_volatilities.append(port_vol * 100)
        
        sharpe = (port_return - 0.005) / port_vol if port_vol > 0 else 0
        portfolio_sharpes.append(sharpe)
    
    # Calculate current portfolio position
    if holdings:
        total_value = sum(h['current_value'] for h in holdings)
        current_return = 0
        current_vol_sq = 0
        
        for h in holdings:
            weight = h['current_value'] / total_value
            security = get_security_by_ticker(h['ticker'])
            if security:
                exp_return = security['expected_return']
                volatility = security['volatility']
            else:
                fund_info = FUND_DEFINITIONS.get(h['ticker'], {})
                exp_return = fund_info.get('base_return', 0.05)
                volatility = fund_info.get('volatility', 0.15)
            
            current_return += weight * exp_return
            current_vol_sq += (weight * volatility) ** 2
        
        current_vol = np.sqrt(current_vol_sq)
    else:
        current_return = 0.05
        current_vol = 0.15
    
    # Create scatter plot
    fig = go.Figure()
    
    # Random portfolios
    fig.add_trace(go.Scatter(
        x=portfolio_volatilities,
        y=portfolio_returns,
        mode='markers',
        marker=dict(
            size=5,
            color=portfolio_sharpes,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='シャープレシオ')
        ),
        name='ランダムポートフォリオ',
        hovertemplate='リスク: %{x:.1f}%<br>リターン: %{y:.1f}%<extra></extra>'
    ))
    
    # Current portfolio
    fig.add_trace(go.Scatter(
        x=[current_vol * 100],
        y=[current_return * 100],
        mode='markers',
        marker=dict(size=15, color='red', symbol='star'),
        name='現在のポートフォリオ',
        hovertemplate='現在のポートフォリオ<br>リスク: %{x:.1f}%<br>リターン: %{y:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title="効率的フロンティア",
        xaxis_title="リスク（年率ボラティリティ %）",
        yaxis_title="期待リターン（年率 %）",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Analysis
    current_sharpe = (current_return - 0.005) / current_vol if current_vol > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("現在の期待リターン", f"{current_return * 100:.1f}%")
    with col2:
        st.metric("現在のリスク", f"{current_vol * 100:.1f}%")
    with col3:
        st.metric("現在のシャープレシオ", f"{current_sharpe:.2f}")
    
    # Efficiency assessment
    max_sharpe = max(portfolio_sharpes)
    if current_sharpe >= max_sharpe * 0.9:
        st.success("現在のポートフォリオは効率的フロンティア付近にあります")
    elif current_sharpe >= max_sharpe * 0.7:
        st.warning("現在のポートフォリオは改善の余地があります")
    else:
        st.error("現在のポートフォリオは非効率的です。リバランスを検討してください。")


def render_fund_depletion_simulation(holdings: List[Dict]):
    """Render fund depletion simulation with warnings."""
    st.markdown("### 資金枯渇シミュレーション")
    st.markdown("現在の資産と支出計画に基づいて、資金が枯渇する時期を予測します")
    
    import plotly.graph_objects as go
    
    # Get user profile data
    profile = st.session_state.user_profile
    retirement = st.session_state.retirement_plan
    
    current_age = profile['personal']['age']
    retirement_age = retirement['target_age']
    annual_expense = retirement['annual_expense']
    monthly_investment = profile['cashflow'].get('monthly_investment', 0)
    annual_investment = monthly_investment * 12
    
    # Calculate current total assets
    savings = profile['assets'].get('savings', 0)
    portfolio_value = sum(h['current_value'] for h in holdings)
    total_assets = savings + portfolio_value
    
    # Simulation parameters
    years_to_simulate = 50
    expected_return = 0.05  # Default expected return
    
    # Calculate weighted expected return from portfolio
    if holdings:
        total_value = sum(h['current_value'] for h in holdings)
        if total_value > 0:
            weighted_return = 0
            for h in holdings:
                weight = h['current_value'] / total_value
                security = get_security_by_ticker(h['ticker'])
                if security:
                    exp_return = security['expected_return']
                else:
                    fund_info = FUND_DEFINITIONS.get(h['ticker'], {})
                    exp_return = fund_info.get('base_return', 0.05)
                weighted_return += weight * exp_return
            expected_return = weighted_return
    
    # Simulation
    ages = list(range(current_age, current_age + years_to_simulate + 1))
    asset_values = [total_assets]
    
    current_value = total_assets
    depletion_age = None
    
    for year in range(1, years_to_simulate + 1):
        age = current_age + year
        
        # Before retirement: accumulation phase
        if age <= retirement_age:
            # Add investment and growth
            current_value = current_value * (1 + expected_return) + annual_investment
        else:
            # After retirement: withdrawal phase
            current_value = current_value * (1 + expected_return) - annual_expense
        
        asset_values.append(max(0, current_value))
        
        if current_value <= 0 and depletion_age is None:
            depletion_age = age
    
    # Create chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=ages,
        y=asset_values,
        mode='lines',
        name='資産推移',
        fill='tozeroy',
        line=dict(color='blue', width=2)
    ))
    
    # Add retirement line
    fig.add_vline(
        x=retirement_age,
        line_dash="dash",
        line_color="green",
        annotation_text=f"リタイア ({retirement_age}歳)",
        annotation_position="top"
    )
    
    # Add depletion warning if applicable
    if depletion_age:
        fig.add_vline(
            x=depletion_age,
            line_dash="dash",
            line_color="red",
            annotation_text=f"資金枯渇 ({depletion_age}歳)",
            annotation_position="top"
        )
    
    # Format Y-axis
    max_val = max(asset_values)
    tickvals, ticktext = get_axis_tickvals_ticktext(0, max_val, num_ticks=6)
    
    fig.update_layout(
        title="資産推移予測",
        xaxis_title="年齢",
        yaxis_title="資産額",
        height=400
    )
    
    fig.update_yaxes(
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("現在の総資産", format_jpy_jpunit(total_assets))
    
    with col2:
        st.metric("リタイア時資産（予測）", format_jpy_jpunit(asset_values[retirement_age - current_age]))
    
    with col3:
        final_value = asset_values[-1]
        st.metric(f"{current_age + years_to_simulate}歳時資産", format_jpy_jpunit(final_value))
    
    with col4:
        if depletion_age:
            st.metric("資金枯渇年齢", f"{depletion_age}歳", delta="要注意", delta_color="inverse")
        else:
            st.metric("資金枯渇", "なし（50年以内）")
    
    # Warnings and recommendations
    if depletion_age:
        years_until_depletion = depletion_age - current_age
        st.error(f"現在の計画では{depletion_age}歳（{years_until_depletion}年後）に資金が枯渇する可能性があります")
        
        # Calculate required additional savings
        shortfall = annual_expense * (current_age + years_to_simulate - depletion_age)
        required_monthly = shortfall / (retirement_age - current_age) / 12
        
        st.markdown("**改善提案:**")
        st.markdown(f"- 月々の積立額を {format_jpy_jpunit(required_monthly)} 増やす")
        st.markdown(f"- リタイア後の年間支出を {format_jpy_jpunit(annual_expense * 0.8)} に抑える")
        st.markdown(f"- リタイア年齢を {retirement_age + 5}歳 に延長する")
    else:
        life_expectancy = 90
        if asset_values[life_expectancy - current_age] > 0:
            st.success(f"現在の計画では{life_expectancy}歳まで資金が持続する見込みです")
        else:
            st.warning("長寿リスクに備えて、追加の資産形成を検討してください")


def main():
    """Main page entry point."""
    initialize_dashboard_session_state()
    
    st.title("現状分析ダッシュボード")
    st.markdown("ポートフォリオの現状分析と将来予測を行います")
    
    st.page_link("app.py", label="ポートフォリオ入力に戻る", icon="🏠")
    
    st.markdown("---")
    
    # Portfolio input section
    with st.expander("ポートフォリオ入力", expanded=True):
        holdings = render_portfolio_input()
        
        if st.button("ポートフォリオを保存", type="primary"):
            st.session_state.current_portfolio = holdings
            st.success("ポートフォリオを保存しました")
    
    st.markdown("---")
    
    # Use saved portfolio for analysis
    analysis_holdings = st.session_state.current_portfolio if st.session_state.current_portfolio else holdings
    
    # Summary
    render_portfolio_summary(analysis_holdings)
    
    st.markdown("---")
    
    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "相関分析", "バックテスト", "効率的フロンティア", "資金枯渇シミュレーション"
    ])
    
    with tab1:
        render_correlation_heatmap(analysis_holdings)
    
    with tab2:
        render_backtest_chart(analysis_holdings)
    
    with tab3:
        render_efficient_frontier(analysis_holdings)
    
    with tab4:
        render_fund_depletion_simulation(analysis_holdings)
    
    st.markdown("---")
    
    # Navigation
    st.markdown("### 次のステップ")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link(
            "pages/04_ライフイベント計画.py",
            label="ライフイベント計画へ",
            icon="📅"
        )
    with col2:
        st.page_link(
            "pages/05_資産シミュレーション.py",
            label="資産シミュレーションへ",
            icon="📊"
        )
    with col3:
        st.page_link(
            "pages/07_戦略提案ダッシュボード.py",
            label="戦略提案へ",
            icon="💡"
        )


if __name__ == "__main__":
    main()
