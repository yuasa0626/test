"""
Stress Test Page
Provides stress testing with historical crash scenarios including:
- Lehman Shock (2008)
- COVID-19 Crash (2020)
- IT Bubble Burst (2000)
- Custom stress scenarios
Shows maximum loss amount and recovery time estimates.
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
from models.securities_master import get_security_by_ticker, ASSET_CLASSES
from data_fetcher import FUND_DEFINITIONS

# Page configuration
st.set_page_config(
    page_title="ストレステスト",
    page_icon="⚠️",
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

# Historical crisis scenarios
CRISIS_SCENARIOS = {
    'lehman': {
        'name': 'リーマンショック（2008年）',
        'description': '2008年9月のリーマン・ブラザーズ破綻に端を発した世界金融危機',
        'period': '2008年9月〜2009年3月',
        'duration_months': 6,
        'recovery_months': 48,  # Time to recover to pre-crisis levels
        'asset_impacts': {
            'domestic_stock': -0.51,  # TOPIX fell ~51%
            'foreign_stock': -0.57,   # S&P500 fell ~57%
            'domestic_bond': 0.02,    # Slight gain (flight to safety)
            'foreign_bond': -0.05,    # Slight loss
            'reit': -0.65,            # REITs fell ~65%
            'emerging_stock': -0.62,  # Emerging markets fell ~62%
        },
        'daily_volatility_multiplier': 3.0,  # Volatility increased 3x
    },
    'covid': {
        'name': 'コロナショック（2020年）',
        'description': '2020年2月〜3月のCOVID-19パンデミックによる急落',
        'period': '2020年2月〜2020年3月',
        'duration_months': 1.5,
        'recovery_months': 6,  # V-shaped recovery
        'asset_impacts': {
            'domestic_stock': -0.31,  # TOPIX fell ~31%
            'foreign_stock': -0.34,   # S&P500 fell ~34%
            'domestic_bond': 0.01,    # Slight gain
            'foreign_bond': -0.02,    # Slight loss
            'reit': -0.35,            # REITs fell ~35%
            'emerging_stock': -0.32,  # Emerging markets fell ~32%
        },
        'daily_volatility_multiplier': 4.0,  # Extreme volatility
    },
    'dotcom': {
        'name': 'ITバブル崩壊（2000年）',
        'description': '2000年3月のドットコムバブル崩壊',
        'period': '2000年3月〜2002年10月',
        'duration_months': 31,
        'recovery_months': 84,  # Long recovery
        'asset_impacts': {
            'domestic_stock': -0.63,  # TOPIX fell ~63%
            'foreign_stock': -0.49,   # S&P500 fell ~49%
            'domestic_bond': 0.05,    # Gain (flight to safety)
            'foreign_bond': 0.03,     # Slight gain
            'reit': -0.20,            # REITs fell ~20%
            'emerging_stock': -0.45,  # Emerging markets fell ~45%
        },
        'daily_volatility_multiplier': 2.0,
    },
    'japan_bubble': {
        'name': '日本バブル崩壊（1990年）',
        'description': '1990年の日本資産バブル崩壊',
        'period': '1990年1月〜1992年8月',
        'duration_months': 32,
        'recovery_months': 360,  # Still not fully recovered
        'asset_impacts': {
            'domestic_stock': -0.63,  # Nikkei fell ~63%
            'foreign_stock': -0.10,   # US stocks relatively stable
            'domestic_bond': 0.08,    # Gain
            'foreign_bond': 0.05,     # Gain
            'reit': -0.70,            # Japanese REITs devastated
            'emerging_stock': -0.15,  # Moderate impact
        },
        'daily_volatility_multiplier': 2.5,
    },
    'custom': {
        'name': 'カスタムシナリオ',
        'description': 'ユーザー定義のストレスシナリオ',
        'period': 'カスタム',
        'duration_months': 6,
        'recovery_months': 24,
        'asset_impacts': {
            'domestic_stock': -0.30,
            'foreign_stock': -0.30,
            'domestic_bond': 0.00,
            'foreign_bond': 0.00,
            'reit': -0.30,
            'emerging_stock': -0.30,
        },
        'daily_volatility_multiplier': 2.0,
    }
}


def initialize_stress_test_session_state():
    """Initialize session state for stress tests."""
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
    if 'stress_test_results' not in st.session_state:
        st.session_state.stress_test_results = {}


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
        return 'foreign_stock'  # Default


def calculate_portfolio_stress_impact(
    holdings: List[Dict],
    scenario: Dict
) -> Dict:
    """Calculate stress impact on portfolio."""
    if not holdings:
        return {
            'total_loss': 0,
            'loss_percentage': 0,
            'holdings_impact': [],
            'recovery_time': 0
        }
    
    total_value = sum(h.get('current_value', 0) for h in holdings)
    asset_impacts = scenario['asset_impacts']
    
    holdings_impact = []
    total_loss = 0
    
    for h in holdings:
        current_value = h.get('current_value', 0)
        asset_class = get_asset_class_for_holding(h)
        
        # Get impact for this asset class
        impact = asset_impacts.get(asset_class, -0.30)  # Default -30%
        
        loss = current_value * abs(impact)
        post_crisis_value = current_value * (1 + impact)
        
        holdings_impact.append({
            'ticker': h.get('ticker', ''),
            'name': h.get('name', ''),
            'current_value': current_value,
            'asset_class': asset_class,
            'impact_pct': impact,
            'loss': loss,
            'post_crisis_value': max(0, post_crisis_value)
        })
        
        total_loss += loss
    
    loss_percentage = total_loss / total_value if total_value > 0 else 0
    
    return {
        'total_value': total_value,
        'total_loss': total_loss,
        'loss_percentage': loss_percentage,
        'post_crisis_value': total_value - total_loss,
        'holdings_impact': holdings_impact,
        'recovery_months': scenario['recovery_months'],
        'duration_months': scenario['duration_months']
    }


def simulate_crisis_path(
    initial_value: float,
    scenario: Dict,
    holdings: List[Dict],
    days: int = 252
) -> Tuple[List[float], List[float]]:
    """Simulate daily portfolio values during crisis."""
    np.random.seed(42)
    
    # Calculate weighted impact
    total_value = sum(h.get('current_value', 0) for h in holdings)
    weighted_impact = 0
    
    for h in holdings:
        weight = h.get('current_value', 0) / total_value if total_value > 0 else 0
        asset_class = get_asset_class_for_holding(h)
        impact = scenario['asset_impacts'].get(asset_class, -0.30)
        weighted_impact += weight * impact
    
    # Generate crisis path
    duration_days = int(scenario['duration_months'] * 21)  # ~21 trading days per month
    recovery_days = int(scenario['recovery_months'] * 21)
    
    # Crisis phase - gradual decline with high volatility
    crisis_values = [initial_value]
    daily_decline = weighted_impact / duration_days
    vol_multiplier = scenario['daily_volatility_multiplier']
    base_vol = 0.01  # Base daily volatility
    
    current_value = initial_value
    for day in range(1, min(duration_days, days) + 1):
        # Add noise to decline
        noise = np.random.normal(0, base_vol * vol_multiplier)
        daily_return = daily_decline + noise
        current_value = current_value * (1 + daily_return)
        crisis_values.append(max(0, current_value))
    
    # Recovery phase
    bottom_value = crisis_values[-1]
    target_value = initial_value
    recovery_rate = (target_value / bottom_value) ** (1 / recovery_days) - 1 if bottom_value > 0 else 0
    
    recovery_values = [bottom_value]
    current_value = bottom_value
    
    for day in range(1, min(recovery_days, days - duration_days) + 1):
        noise = np.random.normal(0, base_vol * 1.5)  # Still elevated volatility
        daily_return = recovery_rate + noise
        current_value = current_value * (1 + daily_return)
        recovery_values.append(min(target_value * 1.1, current_value))  # Cap at 110% of initial
    
    return crisis_values, recovery_values


def render_scenario_selector():
    """Render crisis scenario selector."""
    st.markdown("### ストレスシナリオ選択")
    
    scenario_options = list(CRISIS_SCENARIOS.keys())
    scenario_names = {k: v['name'] for k, v in CRISIS_SCENARIOS.items()}
    
    selected_scenario = st.selectbox(
        "シナリオを選択",
        options=scenario_options,
        format_func=lambda x: scenario_names[x],
        key="stress_scenario"
    )
    
    scenario = CRISIS_SCENARIOS[selected_scenario].copy()
    
    # Show scenario details
    st.markdown(f"**{scenario['name']}**")
    st.markdown(scenario['description'])
    st.markdown(f"期間: {scenario['period']}")
    
    # Custom scenario adjustments
    if selected_scenario == 'custom':
        st.markdown("---")
        st.markdown("**カスタムシナリオ設定**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            scenario['duration_months'] = st.slider(
                "下落期間（月）",
                min_value=1,
                max_value=36,
                value=6,
                key="custom_duration"
            )
            
            scenario['recovery_months'] = st.slider(
                "回復期間（月）",
                min_value=1,
                max_value=120,
                value=24,
                key="custom_recovery"
            )
        
        with col2:
            st.markdown("**資産クラス別下落率**")
            
            for asset_class in ['domestic_stock', 'foreign_stock', 'domestic_bond', 'foreign_bond', 'reit']:
                asset_name = {
                    'domestic_stock': '国内株式',
                    'foreign_stock': '外国株式',
                    'domestic_bond': '国内債券',
                    'foreign_bond': '外国債券',
                    'reit': 'REIT'
                }[asset_class]
                
                impact = st.slider(
                    f"{asset_name}",
                    min_value=-80,
                    max_value=20,
                    value=int(scenario['asset_impacts'][asset_class] * 100),
                    format="%d%%",
                    key=f"custom_impact_{asset_class}"
                )
                scenario['asset_impacts'][asset_class] = impact / 100
    
    return scenario


def render_stress_test_results(holdings: List[Dict], scenario: Dict):
    """Render stress test results."""
    st.markdown("### ストレステスト結果")
    
    if not holdings:
        st.warning("ポートフォリオが登録されていません。現状分析ダッシュボードで登録してください。")
        return
    
    # Calculate impact
    impact = calculate_portfolio_stress_impact(holdings, scenario)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "現在の評価額",
            format_jpy_jpunit(impact['total_value'])
        )
    
    with col2:
        st.metric(
            "最大損失額",
            format_jpy_jpunit(impact['total_loss']),
            f"-{impact['loss_percentage'] * 100:.1f}%",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "危機後評価額",
            format_jpy_jpunit(impact['post_crisis_value'])
        )
    
    with col4:
        st.metric(
            "回復予想期間",
            f"{impact['recovery_months']}ヶ月",
            f"約{impact['recovery_months'] / 12:.1f}年"
        )
    
    # Detailed impact by holding
    st.markdown("---")
    st.markdown("**銘柄別影響**")
    
    impact_data = [
        {
            '銘柄': h['name'][:25] if h['name'] else h['ticker'],
            '現在評価額': format_jpy_jpunit(h['current_value']),
            '下落率': f"{h['impact_pct'] * 100:+.1f}%",
            '損失額': format_jpy_jpunit(h['loss']),
            '危機後評価額': format_jpy_jpunit(h['post_crisis_value'])
        }
        for h in impact['holdings_impact']
    ]
    
    st.dataframe(pd.DataFrame(impact_data), use_container_width=True, hide_index=True)
    
    # Crisis simulation chart
    st.markdown("---")
    st.markdown("**危機シミュレーション**")
    
    import plotly.graph_objects as go
    
    crisis_values, recovery_values = simulate_crisis_path(
        impact['total_value'],
        scenario,
        holdings
    )
    
    # Create timeline
    total_days = len(crisis_values) + len(recovery_values) - 1
    days = list(range(total_days))
    values = crisis_values + recovery_values[1:]
    
    fig = go.Figure()
    
    # Portfolio value line
    fig.add_trace(go.Scatter(
        x=days,
        y=values,
        mode='lines',
        name='ポートフォリオ価値',
        line=dict(color='blue', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 100, 255, 0.1)'
    ))
    
    # Add markers for key points
    fig.add_trace(go.Scatter(
        x=[0],
        y=[impact['total_value']],
        mode='markers',
        name='危機前',
        marker=dict(size=12, color='green', symbol='circle')
    ))
    
    fig.add_trace(go.Scatter(
        x=[len(crisis_values) - 1],
        y=[min(crisis_values)],
        mode='markers',
        name='底値',
        marker=dict(size=12, color='red', symbol='circle')
    ))
    
    # Format Y-axis
    max_val = max(values)
    min_val = min(values)
    tickvals, ticktext = get_axis_tickvals_ticktext(min_val * 0.9, max_val * 1.1, num_ticks=6)
    
    fig.update_layout(
        title=f"{scenario['name']} シミュレーション",
        xaxis_title="日数",
        yaxis_title="ポートフォリオ価値",
        height=400,
        showlegend=True
    )
    
    fig.update_yaxes(
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk assessment
    st.markdown("---")
    st.markdown("**リスク評価**")
    
    # Calculate risk metrics
    emergency_fund = st.session_state.user_profile['assets'].get('emergency_fund', 0)
    monthly_expense = st.session_state.user_profile['cashflow'].get('annual_expense', 3000000) / 12
    
    months_covered = emergency_fund / monthly_expense if monthly_expense > 0 else 0
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**緊急予備資金の評価**")
        st.metric("緊急予備資金", format_jpy_jpunit(emergency_fund))
        st.metric("生活費カバー期間", f"{months_covered:.1f}ヶ月")
        
        if months_covered >= 6:
            st.success("緊急予備資金は十分です（6ヶ月以上）")
        elif months_covered >= 3:
            st.warning("緊急予備資金を増やすことを検討してください（3-6ヶ月）")
        else:
            st.error("緊急予備資金が不足しています（3ヶ月未満）")
    
    with col2:
        st.markdown("**危機時の対応力**")
        
        # Can survive crisis without selling?
        crisis_duration_months = scenario['duration_months']
        required_funds = monthly_expense * crisis_duration_months
        
        if emergency_fund >= required_funds:
            st.success(f"危機期間（{crisis_duration_months}ヶ月）を投資資産を売却せずに乗り切れます")
        else:
            shortfall = required_funds - emergency_fund
            st.warning(f"危機期間を乗り切るには追加で{format_jpy_jpunit(shortfall)}が必要です")
        
        # Recovery time assessment
        if impact['recovery_months'] <= 12:
            st.info("回復期間は比較的短期（1年以内）です")
        elif impact['recovery_months'] <= 36:
            st.info("回復期間は中期（1-3年）です")
        else:
            st.warning("回復期間は長期（3年以上）です。長期投資の視点が重要です")
    
    # Save results
    st.session_state.stress_test_results[scenario['name']] = impact
    
    return impact


def render_scenario_comparison():
    """Render comparison of multiple stress scenarios."""
    st.markdown("### シナリオ比較")
    
    holdings = st.session_state.current_portfolio
    
    if not holdings:
        st.info("ポートフォリオが登録されていません")
        return
    
    # Calculate impact for all scenarios
    comparison_data = []
    
    for scenario_id, scenario in CRISIS_SCENARIOS.items():
        if scenario_id == 'custom':
            continue
        
        impact = calculate_portfolio_stress_impact(holdings, scenario)
        
        comparison_data.append({
            'シナリオ': scenario['name'],
            '下落率': f"{impact['loss_percentage'] * 100:.1f}%",
            '最大損失額': format_jpy_jpunit(impact['total_loss']),
            '危機後評価額': format_jpy_jpunit(impact['post_crisis_value']),
            '回復期間': f"{impact['recovery_months']}ヶ月"
        })
    
    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
    
    # Bar chart comparison
    import plotly.graph_objects as go
    
    scenarios = [d['シナリオ'] for d in comparison_data]
    losses = [calculate_portfolio_stress_impact(holdings, CRISIS_SCENARIOS[sid])['loss_percentage'] * 100 
              for sid in ['lehman', 'covid', 'dotcom', 'japan_bubble']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=scenarios,
            y=losses,
            marker_color=['red', 'orange', 'yellow', 'purple']
        )
    ])
    
    fig.update_layout(
        title="シナリオ別下落率比較",
        xaxis_title="シナリオ",
        yaxis_title="下落率（%）",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_recommendations(impact: Dict, scenario: Dict):
    """Render recommendations based on stress test results."""
    st.markdown("### 推奨アクション")
    
    loss_pct = impact['loss_percentage']
    recovery_months = impact['recovery_months']
    
    recommendations = []
    
    # Based on loss severity
    if loss_pct > 0.5:
        recommendations.append({
            'priority': '高',
            'category': 'リスク軽減',
            'action': '債券比率を増やしてポートフォリオのリスクを軽減することを検討してください',
            'reason': f'現在のポートフォリオは{scenario["name"]}で{loss_pct*100:.0f}%以上下落する可能性があります'
        })
    elif loss_pct > 0.3:
        recommendations.append({
            'priority': '中',
            'category': 'リスク管理',
            'action': '資産配分の見直しを検討してください',
            'reason': f'下落率{loss_pct*100:.0f}%は許容範囲内か確認が必要です'
        })
    
    # Based on recovery time
    if recovery_months > 60:
        recommendations.append({
            'priority': '高',
            'category': '長期計画',
            'action': '投資期間が回復期間より長いことを確認してください',
            'reason': f'回復に{recovery_months/12:.0f}年以上かかる可能性があります'
        })
    
    # Emergency fund
    emergency_fund = st.session_state.user_profile['assets'].get('emergency_fund', 0)
    monthly_expense = st.session_state.user_profile['cashflow'].get('annual_expense', 3000000) / 12
    months_covered = emergency_fund / monthly_expense if monthly_expense > 0 else 0
    
    if months_covered < 6:
        recommendations.append({
            'priority': '高',
            'category': '緊急予備資金',
            'action': f'緊急予備資金を{format_jpy_jpunit(monthly_expense * 6)}まで増やすことを検討してください',
            'reason': f'現在の緊急予備資金は{months_covered:.1f}ヶ月分のみです'
        })
    
    # Diversification
    holdings = st.session_state.current_portfolio
    if holdings:
        asset_classes = set(get_asset_class_for_holding(h) for h in holdings)
        if len(asset_classes) < 3:
            recommendations.append({
                'priority': '中',
                'category': '分散投資',
                'action': '資産クラスの分散を検討してください',
                'reason': f'現在{len(asset_classes)}種類の資産クラスのみに投資しています'
            })
    
    if recommendations:
        for rec in recommendations:
            priority_color = {'高': 'red', '中': 'orange', '低': 'green'}[rec['priority']]
            st.markdown(f"""
            **[{rec['priority']}優先度] {rec['category']}**
            - アクション: {rec['action']}
            - 理由: {rec['reason']}
            """)
    else:
        st.success("現在のポートフォリオは適切にリスク管理されています")
    
    st.caption("※これは簡易モデルによる参考値です。実際の投資判断は専門家にご相談ください。")


def main():
    """Main page entry point."""
    initialize_stress_test_session_state()
    
    st.title("ストレステスト")
    st.markdown("歴史的な危機シナリオに基づいてポートフォリオの耐久性を評価します")
    
    st.page_link("app.py", label="ポートフォリオ入力に戻る", icon="🏠")
    
    st.markdown("---")
    
    # Scenario selection
    scenario = render_scenario_selector()
    
    st.markdown("---")
    
    # Run stress test
    if st.button("ストレステスト実行", type="primary"):
        holdings = st.session_state.current_portfolio
        impact = render_stress_test_results(holdings, scenario)
        
        if impact and impact['total_loss'] > 0:
            st.markdown("---")
            render_recommendations(impact, scenario)
    
    st.markdown("---")
    
    # Scenario comparison
    with st.expander("全シナリオ比較", expanded=False):
        render_scenario_comparison()
    
    st.markdown("---")
    
    # Navigation
    st.markdown("### 次のステップ")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link(
            "pages/07_戦略提案ダッシュボード.py",
            label="戦略提案に戻る",
            icon="💡"
        )
    with col2:
        st.page_link(
            "pages/06_現状分析ダッシュボード.py",
            label="現状分析に戻る",
            icon="📊"
        )
    with col3:
        st.page_link(
            "pages/09_統合ダッシュボード.py",
            label="統合ダッシュボードへ",
            icon="📈"
        )


if __name__ == "__main__":
    main()
