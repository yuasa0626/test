"""
Strategy Proposal Dashboard Page
Provides investment strategy recommendations including:
- Goal-based optimal portfolio proposal
- Rebalancing recommendations with quantified improvements
- NISA asset location optimization
- Inflation-adjusted Monte Carlo simulation
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.formatters import format_jpy_plain, format_jpy_jpunit, format_jpy_axis, get_axis_tickvals_ticktext
from models.securities_master import (
    search_securities, get_security_by_ticker, get_all_securities,
    ASSET_CLASSES, ACCOUNT_TYPES
)
from data_fetcher import FUND_DEFINITIONS

# Page configuration
st.set_page_config(
    page_title="戦略提案ダッシュボード",
    page_icon="💡",
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


def initialize_strategy_session_state():
    """Initialize session state for strategy dashboard."""
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
    if 'life_events' not in st.session_state:
        st.session_state.life_events = []
    if 'education_plans' not in st.session_state:
        st.session_state.education_plans = []


def calculate_required_return(
    current_assets: float,
    target_assets: float,
    years: int,
    annual_contribution: float
) -> float:
    """
    Calculate required annual return to reach target assets.
    Uses iterative approach to solve for return rate.
    """
    if years <= 0 or current_assets <= 0:
        return 0.0
    
    # Binary search for required return
    low, high = -0.5, 0.5
    
    for _ in range(100):
        mid = (low + high) / 2
        
        # Calculate future value with this return
        fv = current_assets
        for _ in range(years):
            fv = fv * (1 + mid) + annual_contribution
        
        if fv < target_assets:
            low = mid
        else:
            high = mid
        
        if abs(fv - target_assets) < 1000:
            break
    
    return mid


def generate_optimal_portfolio(
    target_return: float,
    risk_tolerance: str = 'moderate'
) -> Dict:
    """
    Generate optimal portfolio allocation based on target return and risk tolerance.
    Uses simplified mean-variance optimization.
    """
    # Asset class expected returns and volatilities
    asset_classes = {
        'domestic_stock': {'return': 0.05, 'vol': 0.18, 'name': '国内株式'},
        'foreign_stock': {'return': 0.08, 'vol': 0.20, 'name': '外国株式'},
        'domestic_bond': {'return': 0.01, 'vol': 0.03, 'name': '国内債券'},
        'foreign_bond': {'return': 0.02, 'vol': 0.08, 'name': '外国債券'},
        'reit': {'return': 0.04, 'vol': 0.15, 'name': 'REIT'},
    }
    
    # Risk tolerance adjustments
    risk_multipliers = {
        'conservative': 0.5,
        'moderate': 1.0,
        'aggressive': 1.5
    }
    
    risk_mult = risk_multipliers.get(risk_tolerance, 1.0)
    
    # Simple allocation based on target return
    if target_return <= 0.02:
        # Conservative
        allocation = {
            'domestic_bond': 0.50,
            'foreign_bond': 0.20,
            'domestic_stock': 0.15,
            'foreign_stock': 0.10,
            'reit': 0.05
        }
    elif target_return <= 0.05:
        # Moderate
        allocation = {
            'domestic_stock': 0.25,
            'foreign_stock': 0.30,
            'domestic_bond': 0.20,
            'foreign_bond': 0.15,
            'reit': 0.10
        }
    else:
        # Aggressive
        allocation = {
            'foreign_stock': 0.50,
            'domestic_stock': 0.25,
            'reit': 0.10,
            'foreign_bond': 0.10,
            'domestic_bond': 0.05
        }
    
    # Calculate expected return and volatility
    expected_return = sum(
        allocation[ac] * asset_classes[ac]['return']
        for ac in allocation
    )
    
    expected_vol = np.sqrt(sum(
        (allocation[ac] * asset_classes[ac]['vol']) ** 2
        for ac in allocation
    ))
    
    # Recommend specific funds
    fund_recommendations = []
    for ac, weight in allocation.items():
        if weight > 0:
            # Find best fund for this asset class
            if ac == 'foreign_stock':
                fund_recommendations.append({
                    'ticker': '03311187',
                    'name': 'eMAXIS Slim 全世界株式（オール・カントリー）',
                    'weight': weight,
                    'asset_class': asset_classes[ac]['name']
                })
            elif ac == 'domestic_stock':
                fund_recommendations.append({
                    'ticker': '03311167',
                    'name': 'eMAXIS Slim 国内株式（TOPIX）',
                    'weight': weight,
                    'asset_class': asset_classes[ac]['name']
                })
            elif ac == 'domestic_bond':
                fund_recommendations.append({
                    'ticker': '03311179',
                    'name': 'eMAXIS Slim 国内債券インデックス',
                    'weight': weight,
                    'asset_class': asset_classes[ac]['name']
                })
            elif ac == 'foreign_bond':
                fund_recommendations.append({
                    'ticker': '03311175',
                    'name': 'eMAXIS Slim 先進国債券インデックス',
                    'weight': weight,
                    'asset_class': asset_classes[ac]['name']
                })
            elif ac == 'reit':
                fund_recommendations.append({
                    'ticker': '03311181',
                    'name': 'eMAXIS Slim 国内リートインデックス',
                    'weight': weight,
                    'asset_class': asset_classes[ac]['name']
                })
    
    return {
        'allocation': allocation,
        'expected_return': expected_return,
        'expected_volatility': expected_vol,
        'sharpe_ratio': (expected_return - 0.005) / expected_vol if expected_vol > 0 else 0,
        'fund_recommendations': fund_recommendations,
        'asset_class_names': {ac: info['name'] for ac, info in asset_classes.items()}
    }


def render_goal_based_proposal():
    """Render goal-based optimal portfolio proposal."""
    st.markdown("### ゴールベース最適ポートフォリオ提案")
    st.markdown("目標達成に必要なリターンを計算し、最適なポートフォリオを提案します")
    
    profile = st.session_state.user_profile
    retirement = st.session_state.retirement_plan
    
    current_age = profile['personal']['age']
    retirement_age = retirement['target_age']
    years_to_retirement = retirement_age - current_age
    
    # Calculate current assets
    savings = profile['assets'].get('savings', 0)
    portfolio_value = sum(h.get('current_value', 0) for h in st.session_state.current_portfolio)
    current_assets = savings + portfolio_value
    
    monthly_investment = profile['cashflow'].get('monthly_investment', 0)
    annual_investment = monthly_investment * 12
    
    # Calculate total life event costs
    education_total = sum(plan.get('remaining_cost', 0) for plan in st.session_state.education_plans)
    other_events_total = sum(e.get('target_amount', 0) for e in st.session_state.life_events)
    total_life_events = education_total + other_events_total
    
    # Calculate target assets at retirement
    annual_expense = retirement['annual_expense']
    years_in_retirement = 30  # Assume 30 years in retirement
    target_assets = annual_expense * years_in_retirement + total_life_events
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**現在の状況**")
        st.metric("現在の総資産", format_jpy_jpunit(current_assets))
        st.metric("年間積立額", format_jpy_jpunit(annual_investment))
        st.metric("リタイアまでの年数", f"{years_to_retirement}年")
    
    with col2:
        st.markdown("**目標**")
        st.metric("目標資産額", format_jpy_jpunit(target_assets))
        st.metric("ライフイベント費用", format_jpy_jpunit(total_life_events))
        st.metric("リタイア後年間生活費", format_jpy_jpunit(annual_expense))
    
    # Calculate required return
    required_return = calculate_required_return(
        current_assets, target_assets, years_to_retirement, annual_investment
    )
    
    st.markdown("---")
    
    st.markdown("**必要リターン分析**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("目標達成に必要な年率リターン", f"{required_return * 100:.1f}%")
    
    with col2:
        if required_return <= 0.03:
            risk_level = "低リスク"
            risk_color = "green"
        elif required_return <= 0.06:
            risk_level = "中リスク"
            risk_color = "orange"
        else:
            risk_level = "高リスク"
            risk_color = "red"
        st.metric("必要リスクレベル", risk_level)
    
    with col3:
        if required_return <= 0.08:
            feasibility = "達成可能"
        elif required_return <= 0.12:
            feasibility = "やや困難"
        else:
            feasibility = "困難"
        st.metric("達成可能性", feasibility)
    
    # Generate optimal portfolio
    risk_tolerance = st.selectbox(
        "リスク許容度",
        options=['conservative', 'moderate', 'aggressive'],
        format_func=lambda x: {'conservative': '保守的', 'moderate': '中程度', 'aggressive': '積極的'}[x],
        index=1
    )
    
    optimal = generate_optimal_portfolio(required_return, risk_tolerance)
    
    st.markdown("---")
    
    st.markdown("**推奨ポートフォリオ**")
    
    import plotly.express as px
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Asset allocation pie chart
        allocation_data = {
            optimal['asset_class_names'][ac]: weight * 100
            for ac, weight in optimal['allocation'].items()
            if weight > 0
        }
        
        fig = px.pie(
            values=list(allocation_data.values()),
            names=list(allocation_data.keys()),
            title="推奨資産配分"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.metric("期待リターン", f"{optimal['expected_return'] * 100:.1f}%")
        st.metric("期待ボラティリティ", f"{optimal['expected_volatility'] * 100:.1f}%")
        st.metric("シャープレシオ", f"{optimal['sharpe_ratio']:.2f}")
    
    # Fund recommendations
    st.markdown("**推奨ファンド**")
    
    fund_data = [
        {
            '銘柄': f['name'],
            '資産クラス': f['asset_class'],
            '配分比率': f"{f['weight'] * 100:.0f}%"
        }
        for f in optimal['fund_recommendations']
    ]
    
    st.dataframe(pd.DataFrame(fund_data), use_container_width=True, hide_index=True)
    
    st.caption("※これは簡易モデルによる参考値です。実際の投資判断は専門家にご相談ください。")
    
    return optimal


def render_rebalancing_recommendations():
    """Render rebalancing recommendations with quantified improvements."""
    st.markdown("### リバランス提案")
    st.markdown("現在のポートフォリオと推奨配分の差異を分析し、具体的な売買提案を行います")
    
    holdings = st.session_state.current_portfolio
    
    if not holdings:
        st.info("ポートフォリオが登録されていません。現状分析ダッシュボードで登録してください。")
        return
    
    # Calculate current allocation
    total_value = sum(h.get('current_value', 0) for h in holdings)
    
    if total_value == 0:
        st.warning("ポートフォリオの評価額が0です")
        return
    
    current_allocation = {}
    for h in holdings:
        security = get_security_by_ticker(h['ticker'])
        if security:
            asset_class = security['asset_class']
        else:
            fund_info = FUND_DEFINITIONS.get(h['ticker'], {})
            # Map fund to asset class
            name = fund_info.get('name', '')
            if '株式' in name:
                if '国内' in name or 'TOPIX' in name or '日経' in name:
                    asset_class = 'domestic_stock'
                else:
                    asset_class = 'foreign_stock'
            elif '債券' in name:
                if '国内' in name:
                    asset_class = 'domestic_bond'
                else:
                    asset_class = 'foreign_bond'
            elif 'リート' in name or 'REIT' in name:
                asset_class = 'reit'
            else:
                asset_class = 'foreign_stock'  # Default
        
        current_allocation[asset_class] = current_allocation.get(asset_class, 0) + h['current_value']
    
    # Convert to percentages
    current_pct = {ac: val / total_value for ac, val in current_allocation.items()}
    
    # Target allocation (moderate)
    target_allocation = {
        'domestic_stock': 0.25,
        'foreign_stock': 0.30,
        'domestic_bond': 0.20,
        'foreign_bond': 0.15,
        'reit': 0.10
    }
    
    asset_class_names = {
        'domestic_stock': '国内株式',
        'foreign_stock': '外国株式',
        'domestic_bond': '国内債券',
        'foreign_bond': '外国債券',
        'reit': 'REIT'
    }
    
    # Calculate differences
    rebalance_actions = []
    
    for ac in target_allocation:
        current = current_pct.get(ac, 0)
        target = target_allocation[ac]
        diff = target - current
        diff_amount = diff * total_value
        
        if abs(diff) > 0.02:  # Only show if difference > 2%
            action = '買い増し' if diff > 0 else '売却'
            rebalance_actions.append({
                'asset_class': ac,
                'asset_class_name': asset_class_names[ac],
                'current_pct': current,
                'target_pct': target,
                'diff_pct': diff,
                'diff_amount': diff_amount,
                'action': action
            })
    
    if not rebalance_actions:
        st.success("現在のポートフォリオは目標配分に近い状態です。リバランスは不要です。")
        return
    
    # Display comparison chart
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    categories = [asset_class_names[ac] for ac in target_allocation]
    current_values = [current_pct.get(ac, 0) * 100 for ac in target_allocation]
    target_values = [target_allocation[ac] * 100 for ac in target_allocation]
    
    fig.add_trace(go.Bar(
        name='現在',
        x=categories,
        y=current_values,
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='目標',
        x=categories,
        y=target_values,
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title="現在 vs 目標配分",
        yaxis_title="配分比率（%）",
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Rebalancing actions table
    st.markdown("**具体的なリバランス提案**")
    
    action_data = [
        {
            '資産クラス': a['asset_class_name'],
            '現在': f"{a['current_pct'] * 100:.1f}%",
            '目標': f"{a['target_pct'] * 100:.1f}%",
            '差異': f"{a['diff_pct'] * 100:+.1f}%",
            'アクション': a['action'],
            '金額': format_jpy_jpunit(abs(a['diff_amount']))
        }
        for a in rebalance_actions
    ]
    
    st.dataframe(pd.DataFrame(action_data), use_container_width=True, hide_index=True)
    
    # Calculate improvement metrics
    # Current portfolio metrics
    current_return = sum(
        current_pct.get(ac, 0) * {'domestic_stock': 0.05, 'foreign_stock': 0.08, 'domestic_bond': 0.01, 'foreign_bond': 0.02, 'reit': 0.04}.get(ac, 0.05)
        for ac in current_pct
    )
    
    current_vol = np.sqrt(sum(
        (current_pct.get(ac, 0) * {'domestic_stock': 0.18, 'foreign_stock': 0.20, 'domestic_bond': 0.03, 'foreign_bond': 0.08, 'reit': 0.15}.get(ac, 0.15)) ** 2
        for ac in current_pct
    ))
    
    # Target portfolio metrics
    target_return = sum(
        target_allocation[ac] * {'domestic_stock': 0.05, 'foreign_stock': 0.08, 'domestic_bond': 0.01, 'foreign_bond': 0.02, 'reit': 0.04}[ac]
        for ac in target_allocation
    )
    
    target_vol = np.sqrt(sum(
        (target_allocation[ac] * {'domestic_stock': 0.18, 'foreign_stock': 0.20, 'domestic_bond': 0.03, 'foreign_bond': 0.08, 'reit': 0.15}[ac]) ** 2
        for ac in target_allocation
    ))
    
    st.markdown("**リバランス効果**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        return_diff = (target_return - current_return) * 100
        st.metric("期待リターン変化", f"{return_diff:+.2f}%")
    
    with col2:
        vol_diff = (target_vol - current_vol) * 100
        st.metric("ボラティリティ変化", f"{vol_diff:+.2f}%")
    
    with col3:
        current_sharpe = (current_return - 0.005) / current_vol if current_vol > 0 else 0
        target_sharpe = (target_return - 0.005) / target_vol if target_vol > 0 else 0
        sharpe_diff = target_sharpe - current_sharpe
        st.metric("シャープレシオ変化", f"{sharpe_diff:+.2f}")
    
    st.caption("※これは簡易モデルによる参考値です。実際の売買は手数料・税金を考慮してください。")


def render_nisa_optimization():
    """Render NISA asset location optimization."""
    st.markdown("### NISAアセットロケーション最適化")
    st.markdown("NISA口座と特定口座の使い分けを最適化し、税制メリットを最大化します")
    
    holdings = st.session_state.current_portfolio
    
    if not holdings:
        st.info("ポートフォリオが登録されていません。現状分析ダッシュボードで登録してください。")
        return
    
    # Analyze current NISA usage
    nisa_holdings = [h for h in holdings if h.get('account_type') in ['nisa_tsumitate', 'nisa_growth', 'nisa_old']]
    tokutei_holdings = [h for h in holdings if h.get('account_type') == 'tokutei']
    
    nisa_total = sum(h.get('current_value', 0) for h in nisa_holdings)
    tokutei_total = sum(h.get('current_value', 0) for h in tokutei_holdings)
    total_value = nisa_total + tokutei_total
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("NISA口座", format_jpy_jpunit(nisa_total))
    
    with col2:
        st.metric("特定口座", format_jpy_jpunit(tokutei_total))
    
    with col3:
        nisa_ratio = nisa_total / total_value * 100 if total_value > 0 else 0
        st.metric("NISA比率", f"{nisa_ratio:.1f}%")
    
    st.markdown("---")
    
    st.markdown("**NISA最適化の原則**")
    st.markdown("""
    1. **高リターン資産をNISAに**: 期待リターンが高い資産（株式等）をNISA口座に配置
    2. **低リターン資産を特定口座に**: 債券等の低リターン資産は特定口座でも税負担が小さい
    3. **つみたて投資枠を優先**: 長期投資に適したインデックスファンドを優先的に配置
    """)
    
    # Analyze each holding
    st.markdown("**現在の配置分析**")
    
    analysis_data = []
    optimization_suggestions = []
    
    for h in holdings:
        ticker = h.get('ticker', '')
        account_type = h.get('account_type', 'tokutei')
        current_value = h.get('current_value', 0)
        
        # Get expected return
        security = get_security_by_ticker(ticker)
        if security:
            exp_return = security['expected_return']
            name = security['name']
        else:
            fund_info = FUND_DEFINITIONS.get(ticker, {})
            exp_return = fund_info.get('base_return', 0.05)
            name = fund_info.get('name', ticker)
        
        # Determine if placement is optimal
        is_high_return = exp_return >= 0.05
        is_in_nisa = account_type in ['nisa_tsumitate', 'nisa_growth', 'nisa_old']
        
        if is_high_return and not is_in_nisa:
            optimal = False
            suggestion = 'NISAへ移動推奨'
            optimization_suggestions.append({
                'name': name,
                'current_account': ACCOUNT_TYPES.get(account_type, account_type),
                'suggested_account': 'NISA',
                'value': current_value,
                'expected_return': exp_return
            })
        elif not is_high_return and is_in_nisa:
            optimal = False
            suggestion = '特定口座でも可'
        else:
            optimal = True
            suggestion = '最適'
        
        analysis_data.append({
            '銘柄': name[:20],
            '口座': ACCOUNT_TYPES.get(account_type, account_type),
            '評価額': format_jpy_jpunit(current_value),
            '期待リターン': f"{exp_return * 100:.1f}%",
            '配置': '最適' if optimal else '要検討',
            '提案': suggestion
        })
    
    st.dataframe(pd.DataFrame(analysis_data), use_container_width=True, hide_index=True)
    
    # Calculate tax savings potential
    if optimization_suggestions:
        st.markdown("---")
        st.markdown("**最適化による税制メリット**")
        
        # Calculate potential tax savings over 20 years
        years = 20
        tax_rate = 0.20315  # 20.315% capital gains tax
        
        total_tax_savings = 0
        
        for s in optimization_suggestions:
            value = s['value']
            exp_return = s['expected_return']
            
            # Calculate future value
            future_value = value * ((1 + exp_return) ** years)
            gain = future_value - value
            
            # Tax on gain if in tokutei
            tax_if_tokutei = gain * tax_rate
            
            # No tax if in NISA
            tax_if_nisa = 0
            
            tax_savings = tax_if_tokutei - tax_if_nisa
            total_tax_savings += tax_savings
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "口座の使い分けによる税制メリット（20年後）",
                format_jpy_jpunit(total_tax_savings),
                help="高リターン資産をNISAに移すことで節税できる金額の目安"
            )
        
        with col2:
            st.info(f"NISAへの移動を推奨する銘柄: {len(optimization_suggestions)}件")
        
        # Detailed suggestions
        st.markdown("**具体的な移動提案**")
        
        suggestion_data = [
            {
                '銘柄': s['name'][:20],
                '現在の口座': s['current_account'],
                '推奨口座': s['suggested_account'],
                '評価額': format_jpy_jpunit(s['value'])
            }
            for s in optimization_suggestions
        ]
        
        st.dataframe(pd.DataFrame(suggestion_data), use_container_width=True, hide_index=True)
    else:
        st.success("現在の口座配置は最適化されています")
    
    st.caption("※NISA口座への移動は売却・再購入が必要です。実際の移動は手数料・税金を考慮してください。")


def render_inflation_adjusted_simulation():
    """Render inflation-adjusted Monte Carlo simulation."""
    st.markdown("### インフレ調整付きモンテカルロ・シミュレーション")
    st.markdown("インフレを考慮した実質資産価値の推移を予測します")
    
    import plotly.graph_objects as go
    
    profile = st.session_state.user_profile
    retirement = st.session_state.retirement_plan
    
    current_age = profile['personal']['age']
    retirement_age = retirement['target_age']
    
    # Calculate current assets
    savings = profile['assets'].get('savings', 0)
    portfolio_value = sum(h.get('current_value', 0) for h in st.session_state.current_portfolio)
    initial_assets = savings + portfolio_value
    
    monthly_investment = profile['cashflow'].get('monthly_investment', 0)
    annual_investment = monthly_investment * 12
    annual_expense = retirement['annual_expense']
    
    # Simulation parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        expected_return = st.slider(
            "期待リターン（年率）",
            min_value=0.0,
            max_value=0.15,
            value=0.05,
            step=0.01,
            format="%.1f%%",
            key="sim_return"
        ) 
    
    with col2:
        volatility = st.slider(
            "ボラティリティ（年率）",
            min_value=0.05,
            max_value=0.30,
            value=0.15,
            step=0.01,
            format="%.1f%%",
            key="sim_vol"
        )
    
    with col3:
        inflation_rate = st.slider(
            "インフレ率（年率）",
            min_value=0.0,
            max_value=0.05,
            value=0.02,
            step=0.005,
            format="%.1f%%",
            key="sim_inflation"
        )
    
    num_simulations = st.slider(
        "シミュレーション回数",
        min_value=100,
        max_value=5000,
        value=1000,
        step=100,
        key="sim_count"
    )
    
    years_to_simulate = 50
    
    if st.button("シミュレーション実行", type="primary"):
        with st.spinner("シミュレーション実行中..."):
            np.random.seed(42)
            
            # Run Monte Carlo simulation
            all_nominal_paths = []
            all_real_paths = []
            
            for _ in range(num_simulations):
                nominal_path = [initial_assets]
                real_path = [initial_assets]
                
                current_nominal = initial_assets
                current_real = initial_assets
                inflation_factor = 1.0
                
                for year in range(1, years_to_simulate + 1):
                    age = current_age + year
                    
                    # Random return for this year
                    annual_return = np.random.normal(expected_return, volatility)
                    
                    # Update inflation factor
                    inflation_factor *= (1 + inflation_rate)
                    
                    if age <= retirement_age:
                        # Accumulation phase
                        current_nominal = current_nominal * (1 + annual_return) + annual_investment
                        current_real = current_nominal / inflation_factor
                    else:
                        # Withdrawal phase (adjust expense for inflation)
                        inflation_adjusted_expense = annual_expense * inflation_factor
                        current_nominal = current_nominal * (1 + annual_return) - inflation_adjusted_expense
                        current_real = current_nominal / inflation_factor
                    
                    nominal_path.append(max(0, current_nominal))
                    real_path.append(max(0, current_real))
                
                all_nominal_paths.append(nominal_path)
                all_real_paths.append(real_path)
            
            # Calculate percentiles
            nominal_array = np.array(all_nominal_paths)
            real_array = np.array(all_real_paths)
            
            ages = list(range(current_age, current_age + years_to_simulate + 1))
            
            nominal_median = np.median(nominal_array, axis=0)
            nominal_p10 = np.percentile(nominal_array, 10, axis=0)
            nominal_p90 = np.percentile(nominal_array, 90, axis=0)
            
            real_median = np.median(real_array, axis=0)
            real_p10 = np.percentile(real_array, 10, axis=0)
            real_p90 = np.percentile(real_array, 90, axis=0)
            
            # Create chart
            fig = go.Figure()
            
            # Nominal values
            fig.add_trace(go.Scatter(
                x=ages,
                y=nominal_p90,
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=ages,
                y=nominal_p10,
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(0, 100, 255, 0.2)',
                name='名目値（10-90%タイル）'
            ))
            
            fig.add_trace(go.Scatter(
                x=ages,
                y=nominal_median,
                mode='lines',
                line=dict(color='blue', width=2),
                name='名目値（中央値）'
            ))
            
            # Real values
            fig.add_trace(go.Scatter(
                x=ages,
                y=real_p90,
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=ages,
                y=real_p10,
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(255, 100, 0, 0.2)',
                name='実質値（10-90%タイル）'
            ))
            
            fig.add_trace(go.Scatter(
                x=ages,
                y=real_median,
                mode='lines',
                line=dict(color='red', width=2, dash='dash'),
                name='実質値（中央値）'
            ))
            
            # Retirement line
            fig.add_vline(
                x=retirement_age,
                line_dash="dash",
                line_color="green",
                annotation_text=f"リタイア ({retirement_age}歳)"
            )
            
            # Format Y-axis
            max_val = max(max(nominal_p90), max(real_p90))
            tickvals, ticktext = get_axis_tickvals_ticktext(0, max_val, num_ticks=6)
            
            fig.update_layout(
                title="資産推移予測（名目値 vs 実質値）",
                xaxis_title="年齢",
                yaxis_title="資産額",
                height=500,
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            
            fig.update_yaxes(
                tickmode='array',
                tickvals=tickvals,
                ticktext=ticktext
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary statistics
            st.markdown("**シミュレーション結果サマリー**")
            
            retirement_idx = retirement_age - current_age
            final_idx = -1
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    f"リタイア時資産（名目・中央値）",
                    format_jpy_jpunit(nominal_median[retirement_idx])
                )
            
            with col2:
                st.metric(
                    f"リタイア時資産（実質・中央値）",
                    format_jpy_jpunit(real_median[retirement_idx])
                )
            
            with col3:
                # Calculate probability of depletion
                depletion_count = sum(1 for path in all_nominal_paths if min(path) <= 0)
                depletion_prob = depletion_count / num_simulations * 100
                st.metric("資金枯渇確率", f"{depletion_prob:.1f}%")
            
            with col4:
                # Inflation impact
                inflation_impact = (nominal_median[retirement_idx] - real_median[retirement_idx]) / nominal_median[retirement_idx] * 100 if nominal_median[retirement_idx] > 0 else 0
                st.metric("インフレによる目減り", f"{inflation_impact:.1f}%")
            
            # Warnings
            if depletion_prob > 20:
                st.error(f"資金枯渇リスクが高い状態です（{depletion_prob:.1f}%）。積立額の増加またはリスク許容度の見直しを検討してください。")
            elif depletion_prob > 5:
                st.warning(f"資金枯渇リスクがあります（{depletion_prob:.1f}%）。計画の見直しを検討してください。")
            else:
                st.success(f"資金枯渇リスクは低い状態です（{depletion_prob:.1f}%）")
            
            st.caption("※これはシミュレーションによる参考値です。実際の運用成果を保証するものではありません。")


def main():
    """Main page entry point."""
    initialize_strategy_session_state()
    
    st.title("戦略提案ダッシュボード")
    st.markdown("目標達成のための投資戦略を提案します")
    
    st.page_link("app.py", label="ポートフォリオ入力に戻る", icon="🏠")
    
    st.markdown("---")
    
    # Strategy tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "ゴールベース提案", "リバランス提案", "NISA最適化", "インフレ調整シミュレーション"
    ])
    
    with tab1:
        render_goal_based_proposal()
    
    with tab2:
        render_rebalancing_recommendations()
    
    with tab3:
        render_nisa_optimization()
    
    with tab4:
        render_inflation_adjusted_simulation()
    
    st.markdown("---")
    
    # Navigation
    st.markdown("### 次のステップ")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link(
            "pages/06_現状分析ダッシュボード.py",
            label="現状分析に戻る",
            icon="📊"
        )
    with col2:
        st.page_link(
            "pages/08_ストレステスト.py",
            label="ストレステストへ",
            icon="⚠️"
        )
    with col3:
        st.page_link(
            "pages/09_統合ダッシュボード.py",
            label="統合ダッシュボードへ",
            icon="📈"
        )


if __name__ == "__main__":
    main()
