"""
Integrated Dashboard Page
3-panel dashboard that integrates all components:
- Left panel: Current analysis (portfolio composition, correlation, backtest)
- Center panel: Life plan & simulation (asset projection, cashflow, fund shortage warnings)
- Right panel: Proposals & stress details (rebalancing actions, NISA tax effect, stress test results)
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
from models.securities_master import get_security_by_ticker, ASSET_CLASSES, ACCOUNT_TYPES
from data_fetcher import FUND_DEFINITIONS

# Page configuration
st.set_page_config(
    page_title="統合ダッシュボード",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS to hide number input spinners and style the dashboard
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

/* Dashboard panel styling */
.dashboard-panel {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 15px;
    margin: 5px;
}
</style>
""", unsafe_allow_html=True)


def initialize_dashboard_session_state():
    """Initialize session state for integrated dashboard."""
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
    if 'snapshots' not in st.session_state:
        st.session_state.snapshots = []


def get_asset_class_for_holding(holding: Dict) -> str:
    """Determine asset class for a holding."""
    ticker = holding.get('ticker', '')
    
    security = get_security_by_ticker(ticker)
    if security:
        return security['asset_class']
    
    fund_info = FUND_DEFINITIONS.get(ticker, {})
    name = fund_info.get('name', '')
    
    if '株式' in name:
        if '国内' in name or 'TOPIX' in name or '日経' in name:
            return 'domestic_stock'
        elif '新興国' in name or 'エマージング' in name:
            return 'emerging_stock'
        else:
            return 'foreign_stock'
    elif '債券' in name:
        if '国内' in name:
            return 'domestic_bond'
        else:
            return 'foreign_bond'
    elif 'リート' in name or 'REIT' in name:
        return 'reit'
    else:
        return 'foreign_stock'


def render_left_panel():
    """Render left panel: Current analysis."""
    st.markdown("## 現状分析")
    
    holdings = st.session_state.current_portfolio
    profile = st.session_state.user_profile
    
    # Portfolio summary
    if holdings:
        total_value = sum(h.get('current_value', 0) for h in holdings)
        total_purchase = sum(h.get('purchase_value', 0) for h in holdings)
        total_pnl = total_value - total_purchase
        pnl_pct = (total_pnl / total_purchase * 100) if total_purchase > 0 else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("ポートフォリオ評価額", format_jpy_jpunit(total_value))
        with col2:
            st.metric("損益", format_jpy_jpunit(total_pnl), f"{pnl_pct:+.1f}%")
        
        # Asset allocation pie chart
        import plotly.express as px
        
        asset_allocation = {}
        asset_class_names = {
            'domestic_stock': '国内株式',
            'foreign_stock': '外国株式',
            'domestic_bond': '国内債券',
            'foreign_bond': '外国債券',
            'reit': 'REIT',
            'emerging_stock': '新興国株式'
        }
        
        for h in holdings:
            asset_class = get_asset_class_for_holding(h)
            asset_name = asset_class_names.get(asset_class, asset_class)
            asset_allocation[asset_name] = asset_allocation.get(asset_name, 0) + h.get('current_value', 0)
        
        if asset_allocation:
            fig = px.pie(
                values=list(asset_allocation.values()),
                names=list(asset_allocation.keys()),
                title="資産配分"
            )
            fig.update_layout(height=250, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        
        # Account type breakdown
        account_allocation = {}
        for h in holdings:
            account_name = ACCOUNT_TYPES.get(h.get('account_type', 'tokutei'), '特定口座')
            account_allocation[account_name] = account_allocation.get(account_name, 0) + h.get('current_value', 0)
        
        st.markdown("**口座別配分**")
        for account, value in account_allocation.items():
            pct = value / total_value * 100 if total_value > 0 else 0
            st.markdown(f"- {account}: {format_jpy_jpunit(value)} ({pct:.1f}%)")
        
        # Risk metrics
        st.markdown("---")
        st.markdown("**リスク指標**")
        
        # Calculate weighted expected return and volatility
        weighted_return = 0
        weighted_vol_sq = 0
        
        for h in holdings:
            weight = h.get('current_value', 0) / total_value if total_value > 0 else 0
            security = get_security_by_ticker(h.get('ticker', ''))
            if security:
                exp_return = security['expected_return']
                volatility = security['volatility']
            else:
                fund_info = FUND_DEFINITIONS.get(h.get('ticker', ''), {})
                exp_return = fund_info.get('base_return', 0.05)
                volatility = fund_info.get('volatility', 0.15)
            
            weighted_return += weight * exp_return
            weighted_vol_sq += (weight * volatility) ** 2
        
        weighted_vol = np.sqrt(weighted_vol_sq)
        sharpe = (weighted_return - 0.005) / weighted_vol if weighted_vol > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("期待リターン", f"{weighted_return * 100:.1f}%")
        with col2:
            st.metric("ボラティリティ", f"{weighted_vol * 100:.1f}%")
        with col3:
            st.metric("シャープレシオ", f"{sharpe:.2f}")
    else:
        st.info("ポートフォリオが登録されていません")
        st.page_link("pages/06_現状分析ダッシュボード.py", label="ポートフォリオを登録", icon="📊")
    
    # Total assets summary
    st.markdown("---")
    st.markdown("**総資産**")
    
    savings = profile['assets'].get('savings', 0)
    emergency_fund = profile['assets'].get('emergency_fund', 0)
    portfolio_value = sum(h.get('current_value', 0) for h in holdings)
    total_assets = savings + emergency_fund + portfolio_value
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("預貯金", format_jpy_jpunit(savings))
        st.metric("緊急予備資金", format_jpy_jpunit(emergency_fund))
    with col2:
        st.metric("投資資産", format_jpy_jpunit(portfolio_value))
        st.metric("総資産", format_jpy_jpunit(total_assets))


def render_center_panel():
    """Render center panel: Life plan & simulation."""
    st.markdown("## ライフプラン・シミュレーション")
    
    import plotly.graph_objects as go
    
    profile = st.session_state.user_profile
    retirement = st.session_state.retirement_plan
    holdings = st.session_state.current_portfolio
    
    current_age = profile['personal']['age']
    retirement_age = retirement['target_age']
    years_to_retirement = retirement_age - current_age
    
    # Calculate current assets
    savings = profile['assets'].get('savings', 0)
    portfolio_value = sum(h.get('current_value', 0) for h in holdings)
    initial_assets = savings + portfolio_value
    
    monthly_investment = profile['cashflow'].get('monthly_investment', 0)
    annual_investment = monthly_investment * 12
    annual_expense = retirement['annual_expense']
    
    # Life event costs
    education_total = sum(plan.get('remaining_cost', 0) for plan in st.session_state.education_plans)
    other_events_total = sum(e.get('target_amount', 0) for e in st.session_state.life_events)
    
    # Key metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("現在の年齢", f"{current_age}歳")
        st.metric("リタイア目標", f"{retirement_age}歳")
    with col2:
        st.metric("月間積立額", format_jpy_jpunit(monthly_investment))
        st.metric("リタイア後年間生活費", format_jpy_jpunit(annual_expense))
    
    # Life event summary
    st.markdown("---")
    st.markdown("**ライフイベント費用**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("教育費", format_jpy_jpunit(education_total))
    with col2:
        st.metric("その他イベント", format_jpy_jpunit(other_events_total))
    with col3:
        st.metric("合計", format_jpy_jpunit(education_total + other_events_total))
    
    # Asset projection chart
    st.markdown("---")
    st.markdown("**資産推移予測**")
    
    # Simple projection
    expected_return = 0.05
    years_to_simulate = 40
    
    ages = list(range(current_age, current_age + years_to_simulate + 1))
    asset_values = [initial_assets]
    
    current_value = initial_assets
    depletion_age = None
    
    for year in range(1, years_to_simulate + 1):
        age = current_age + year
        
        if age <= retirement_age:
            current_value = current_value * (1 + expected_return) + annual_investment
        else:
            current_value = current_value * (1 + expected_return) - annual_expense
        
        asset_values.append(max(0, current_value))
        
        if current_value <= 0 and depletion_age is None:
            depletion_age = age
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=ages,
        y=asset_values,
        mode='lines',
        name='資産推移',
        fill='tozeroy',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_vline(
        x=retirement_age,
        line_dash="dash",
        line_color="green",
        annotation_text="リタイア"
    )
    
    if depletion_age:
        fig.add_vline(
            x=depletion_age,
            line_dash="dash",
            line_color="red",
            annotation_text="資金枯渇"
        )
    
    max_val = max(asset_values)
    tickvals, ticktext = get_axis_tickvals_ticktext(0, max_val, num_ticks=5)
    
    fig.update_layout(
        xaxis_title="年齢",
        yaxis_title="資産額",
        height=300,
        margin=dict(t=10, b=30, l=0, r=0)
    )
    
    fig.update_yaxes(
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Warnings
    if depletion_age:
        st.error(f"現在の計画では{depletion_age}歳で資金が枯渇する可能性があります")
    else:
        st.success("現在の計画では資金枯渇リスクは低いです")
    
    # Key projections
    st.markdown("**主要予測値**")
    
    retirement_idx = min(retirement_age - current_age, len(asset_values) - 1)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("リタイア時資産（予測）", format_jpy_jpunit(asset_values[retirement_idx]))
    with col2:
        final_idx = min(40, len(asset_values) - 1)
        st.metric(f"{current_age + final_idx}歳時資産", format_jpy_jpunit(asset_values[final_idx]))


def render_right_panel():
    """Render right panel: Proposals & stress details."""
    st.markdown("## 提案・ストレステスト")
    
    holdings = st.session_state.current_portfolio
    profile = st.session_state.user_profile
    
    # Rebalancing summary
    st.markdown("**リバランス提案**")
    
    if holdings:
        total_value = sum(h.get('current_value', 0) for h in holdings)
        
        # Calculate current allocation
        current_allocation = {}
        for h in holdings:
            asset_class = get_asset_class_for_holding(h)
            current_allocation[asset_class] = current_allocation.get(asset_class, 0) + h.get('current_value', 0)
        
        current_pct = {ac: val / total_value for ac, val in current_allocation.items()} if total_value > 0 else {}
        
        # Target allocation
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
        
        # Find significant deviations
        deviations = []
        for ac, target in target_allocation.items():
            current = current_pct.get(ac, 0)
            diff = target - current
            if abs(diff) > 0.05:  # More than 5% deviation
                action = '買い増し' if diff > 0 else '売却'
                deviations.append({
                    'asset_class': asset_class_names.get(ac, ac),
                    'diff': diff,
                    'action': action,
                    'amount': abs(diff * total_value)
                })
        
        if deviations:
            for d in deviations[:3]:  # Show top 3
                st.markdown(f"- **{d['asset_class']}**: {d['action']} {format_jpy_jpunit(d['amount'])}")
        else:
            st.success("ポートフォリオは適切にバランスされています")
    else:
        st.info("ポートフォリオを登録してください")
    
    # NISA optimization summary
    st.markdown("---")
    st.markdown("**NISA最適化**")
    
    if holdings:
        nisa_holdings = [h for h in holdings if h.get('account_type') in ['nisa_tsumitate', 'nisa_growth', 'nisa_old']]
        tokutei_holdings = [h for h in holdings if h.get('account_type') == 'tokutei']
        
        nisa_total = sum(h.get('current_value', 0) for h in nisa_holdings)
        tokutei_total = sum(h.get('current_value', 0) for h in tokutei_holdings)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("NISA", format_jpy_jpunit(nisa_total))
        with col2:
            st.metric("特定口座", format_jpy_jpunit(tokutei_total))
        
        # Check for optimization opportunities
        high_return_in_tokutei = []
        for h in tokutei_holdings:
            security = get_security_by_ticker(h.get('ticker', ''))
            if security:
                exp_return = security['expected_return']
            else:
                fund_info = FUND_DEFINITIONS.get(h.get('ticker', ''), {})
                exp_return = fund_info.get('base_return', 0.05)
            
            if exp_return >= 0.05:
                high_return_in_tokutei.append(h)
        
        if high_return_in_tokutei:
            st.warning(f"{len(high_return_in_tokutei)}銘柄をNISAに移動することで税制メリットを得られます")
        else:
            st.success("NISA口座は最適に活用されています")
    
    # Stress test summary
    st.markdown("---")
    st.markdown("**ストレステスト結果**")
    
    if holdings:
        total_value = sum(h.get('current_value', 0) for h in holdings)
        
        # Simplified stress test results
        scenarios = {
            'リーマンショック': -0.50,
            'コロナショック': -0.32,
            'ITバブル崩壊': -0.45
        }
        
        for scenario, impact in scenarios.items():
            loss = total_value * abs(impact)
            st.markdown(f"- **{scenario}**: -{abs(impact)*100:.0f}% ({format_jpy_jpunit(loss)})")
        
        # Worst case
        worst_loss = total_value * 0.50
        st.metric("最大想定損失", format_jpy_jpunit(worst_loss), "-50%", delta_color="inverse")
    else:
        st.info("ポートフォリオを登録してください")
    
    # Quick actions
    st.markdown("---")
    st.markdown("**詳細分析**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/07_戦略提案ダッシュボード.py", label="戦略提案", icon="💡")
    with col2:
        st.page_link("pages/08_ストレステスト.py", label="ストレステスト", icon="⚠️")


def render_snapshot_section():
    """Render snapshot saving and plan vs actual tracking."""
    st.markdown("---")
    st.markdown("## スナップショット・予実管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**スナップショット保存**")
        
        snapshot_name = st.text_input(
            "スナップショット名",
            value=f"スナップショット_{datetime.now().strftime('%Y%m%d')}",
            key="snapshot_name"
        )
        
        if st.button("現在の状態を保存", type="primary"):
            snapshot = {
                'name': snapshot_name,
                'date': datetime.now().isoformat(),
                'portfolio': st.session_state.current_portfolio.copy(),
                'profile': st.session_state.user_profile.copy(),
                'retirement_plan': st.session_state.retirement_plan.copy(),
                'total_assets': sum(h.get('current_value', 0) for h in st.session_state.current_portfolio) + 
                               st.session_state.user_profile['assets'].get('savings', 0)
            }
            st.session_state.snapshots.append(snapshot)
            st.success(f"スナップショット「{snapshot_name}」を保存しました")
    
    with col2:
        st.markdown("**保存済みスナップショット**")
        
        if st.session_state.snapshots:
            for i, snapshot in enumerate(st.session_state.snapshots[-5:]):  # Show last 5
                date_str = datetime.fromisoformat(snapshot['date']).strftime('%Y/%m/%d')
                st.markdown(f"- {snapshot['name']} ({date_str}): {format_jpy_jpunit(snapshot['total_assets'])}")
        else:
            st.info("保存されたスナップショットはありません")
    
    # Plan vs Actual comparison
    if len(st.session_state.snapshots) >= 2:
        st.markdown("---")
        st.markdown("**予実比較**")
        
        import plotly.graph_objects as go
        
        dates = [datetime.fromisoformat(s['date']) for s in st.session_state.snapshots]
        values = [s['total_assets'] for s in st.session_state.snapshots]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name='実績',
            line=dict(color='blue', width=2)
        ))
        
        # Add planned trajectory (simple linear projection from first snapshot)
        if len(dates) >= 2:
            first_value = values[0]
            expected_return = 0.05
            planned_values = [first_value * ((1 + expected_return) ** ((d - dates[0]).days / 365)) for d in dates]
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=planned_values,
                mode='lines',
                name='計画',
                line=dict(color='gray', width=1, dash='dash')
            ))
        
        max_val = max(values)
        tickvals, ticktext = get_axis_tickvals_ticktext(0, max_val * 1.1, num_ticks=5)
        
        fig.update_layout(
            title="資産推移（実績 vs 計画）",
            xaxis_title="日付",
            yaxis_title="総資産",
            height=300
        )
        
        fig.update_yaxes(
            tickmode='array',
            tickvals=tickvals,
            ticktext=ticktext
        )
        
        st.plotly_chart(fig, use_container_width=True)


def main():
    """Main page entry point."""
    initialize_dashboard_session_state()
    
    st.title("統合ダッシュボード")
    st.markdown("ポートフォリオ分析、ライフプラン、戦略提案を一覧で確認できます")
    
    st.page_link("app.py", label="ポートフォリオ入力に戻る", icon="🏠")
    
    st.markdown("---")
    
    # 3-panel layout
    left_col, center_col, right_col = st.columns([1, 1.5, 1])
    
    with left_col:
        render_left_panel()
    
    with center_col:
        render_center_panel()
    
    with right_col:
        render_right_panel()
    
    # Snapshot section
    render_snapshot_section()
    
    st.markdown("---")
    
    # Navigation to detailed pages
    st.markdown("### 詳細ページ")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.page_link("pages/03_ユーザープロファイル.py", label="プロファイル", icon="👤")
    
    with col2:
        st.page_link("pages/04_ライフイベント計画.py", label="ライフイベント", icon="📅")
    
    with col3:
        st.page_link("pages/06_現状分析ダッシュボード.py", label="現状分析", icon="📊")
    
    with col4:
        st.page_link("pages/05_資産シミュレーション.py", label="シミュレーション", icon="📈")
    
    st.caption("※このダッシュボードは参考値を表示しています。実際の投資判断は専門家にご相談ください。")


if __name__ == "__main__":
    main()
