"""
Asset Projection Simulation Page
Simulates future asset growth based on user profile, life events, and retirement plan.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from typing import Dict, List, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.formatters import format_jpy_plain, format_jpy_jpunit, format_jpy_axis, get_axis_tickvals_ticktext

# Page configuration
st.set_page_config(
    page_title="資産シミュレーション",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def initialize_simulation_session_state():
    """Initialize session state for simulation."""
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {
            'personal': {'age': 30, 'occupation': '会社員'},
            'family': {'has_spouse': False, 'spouse_age': None, 'children': []},
            'cashflow': {'annual_income': 5000000, 'annual_expense': 3000000, 'monthly_investment': 50000},
            'assets': {'savings': 3000000, 'emergency_fund': 1000000},
            'liabilities': []
        }
    if 'life_events' not in st.session_state:
        st.session_state.life_events = []
    if 'retirement_plan' not in st.session_state:
        st.session_state.retirement_plan = {
            'target_age': 65,
            'annual_expense': 3000000,
            'continue_investing': True
        }
    if 'current_portfolio' not in st.session_state:
        st.session_state.current_portfolio = {}


def run_asset_simulation(
    initial_assets: float,
    annual_investment: float,
    expected_return: float,
    volatility: float,
    years: int,
    life_events: List[Dict],
    retirement_age: int,
    current_age: int,
    retirement_expense: float,
    num_simulations: int = 1000
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run Monte Carlo simulation for asset projection.
    
    Returns:
        Tuple of (years_array, simulations_array)
    """
    np.random.seed(42)
    
    years_array = np.arange(0, years + 1)
    simulations = np.zeros((num_simulations, years + 1))
    simulations[:, 0] = initial_assets
    
    event_years = {event['years_from_now']: event['target_amount'] for event in life_events}
    years_to_retirement = retirement_age - current_age
    
    for sim in range(num_simulations):
        for year in range(1, years + 1):
            current_sim_age = current_age + year
            
            random_return = np.random.normal(expected_return, volatility)
            
            prev_value = simulations[sim, year - 1]
            
            growth = prev_value * (1 + random_return)
            
            if current_sim_age <= retirement_age:
                growth += annual_investment
            else:
                growth -= retirement_expense
            
            if year in event_years:
                growth -= event_years[year]
            
            simulations[sim, year] = max(0, growth)
    
    return years_array, simulations


def calculate_percentiles(simulations: np.ndarray) -> Dict[str, np.ndarray]:
    """Calculate percentile paths from simulations."""
    return {
        'p5': np.percentile(simulations, 5, axis=0),
        'p25': np.percentile(simulations, 25, axis=0),
        'p50': np.percentile(simulations, 50, axis=0),
        'p75': np.percentile(simulations, 75, axis=0),
        'p95': np.percentile(simulations, 95, axis=0),
        'mean': np.mean(simulations, axis=0)
    }


def render_simulation_settings():
    """Render simulation settings form."""
    st.markdown("### シミュレーション設定")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        expected_return = st.slider(
            "期待リターン（年率）",
            min_value=0.0,
            max_value=15.0,
            value=5.0,
            step=0.5,
            format="%.1f%%",
            key="sim_return"
        ) / 100
    
    with col2:
        volatility = st.slider(
            "ボラティリティ（年率）",
            min_value=5.0,
            max_value=30.0,
            value=15.0,
            step=1.0,
            format="%.1f%%",
            key="sim_volatility"
        ) / 100
    
    with col3:
        num_simulations = st.slider(
            "シミュレーション回数",
            min_value=100,
            max_value=5000,
            value=1000,
            step=100,
            key="sim_count"
        )
    
    return expected_return, volatility, num_simulations


def render_asset_projection_chart(
    years_array: np.ndarray,
    percentiles: Dict[str, np.ndarray],
    life_events: List[Dict],
    retirement_age: int,
    current_age: int
):
    """Render asset projection chart with percentile bands."""
    st.markdown("### 資産推移シミュレーション")
    
    current_year = datetime.now().year
    years_labels = [current_year + y for y in years_array]
    age_labels = [current_age + y for y in years_array]
    
    # Calculate max value for axis formatting
    max_val = max(percentiles['p95'])
    min_val = 0
    tickvals, ticktext = get_axis_tickvals_ticktext(min_val, max_val, num_ticks=6)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=years_labels,
        y=percentiles['p95'],
        mode='lines',
        name='95パーセンタイル',
        line=dict(width=0),
        showlegend=False,
        hovertemplate='%{customdata}<extra></extra>',
        customdata=[format_jpy_jpunit(v) for v in percentiles['p95']]
    ))
    
    fig.add_trace(go.Scatter(
        x=years_labels,
        y=percentiles['p5'],
        mode='lines',
        name='5-95パーセンタイル範囲',
        fill='tonexty',
        fillcolor='rgba(68, 68, 68, 0.2)',
        line=dict(width=0),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=[format_jpy_jpunit(v) for v in percentiles['p5']]
    ))
    
    fig.add_trace(go.Scatter(
        x=years_labels,
        y=percentiles['p75'],
        mode='lines',
        name='75パーセンタイル',
        line=dict(width=0),
        showlegend=False,
        hovertemplate='%{customdata}<extra></extra>',
        customdata=[format_jpy_jpunit(v) for v in percentiles['p75']]
    ))
    
    fig.add_trace(go.Scatter(
        x=years_labels,
        y=percentiles['p25'],
        mode='lines',
        name='25-75パーセンタイル範囲',
        fill='tonexty',
        fillcolor='rgba(68, 68, 68, 0.4)',
        line=dict(width=0),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=[format_jpy_jpunit(v) for v in percentiles['p25']]
    ))
    
    fig.add_trace(go.Scatter(
        x=years_labels,
        y=percentiles['p50'],
        mode='lines',
        name='中央値（50パーセンタイル）',
        line=dict(color='blue', width=3),
        hovertemplate='中央値: %{customdata}<extra></extra>',
        customdata=[format_jpy_jpunit(v) for v in percentiles['p50']]
    ))
    
    fig.add_trace(go.Scatter(
        x=years_labels,
        y=percentiles['mean'],
        mode='lines',
        name='平均値',
        line=dict(color='green', width=2, dash='dash'),
        hovertemplate='平均値: %{customdata}<extra></extra>',
        customdata=[format_jpy_jpunit(v) for v in percentiles['mean']]
    ))
    
    for event in life_events:
        event_year = current_year + event['years_from_now']
        event_name = event['custom_name'] if event['type'] == 'その他' and event['custom_name'] else event['type']
        fig.add_vline(
            x=event_year,
            line_dash="dot",
            line_color="orange",
            annotation_text=f"{event_name}",
            annotation_position="top"
        )
    
    retirement_year = current_year + (retirement_age - current_age)
    fig.add_vline(
        x=retirement_year,
        line_dash="dash",
        line_color="red",
        annotation_text=f"リタイア ({retirement_age}歳)",
        annotation_position="top"
    )
    
    fig.update_layout(
        title="資産推移予測（モンテカルロ・シミュレーション）",
        xaxis_title="年",
        yaxis_title="資産額",
        hovermode='x unified',
        height=500,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    # Use Japanese format for Y-axis
    fig.update_yaxes(
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_final_value_histogram(simulations: np.ndarray, target_amount: float = None):
    """Render histogram of final asset values."""
    st.markdown("### 最終資産額の分布")
    
    final_values = simulations[:, -1]
    
    # Calculate axis formatting
    max_val = max(final_values)
    min_val = 0
    tickvals, ticktext = get_axis_tickvals_ticktext(min_val, max_val, num_ticks=6)
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=final_values,
        nbinsx=50,
        name='最終資産額',
        marker_color='steelblue',
        opacity=0.7
    ))
    
    mean_val = np.mean(final_values)
    median_val = np.median(final_values)
    
    fig.add_vline(x=mean_val, line_dash="dash", line_color="green",
                  annotation_text=f"平均: {format_jpy_jpunit(mean_val)}")
    fig.add_vline(x=median_val, line_dash="dash", line_color="blue",
                  annotation_text=f"中央値: {format_jpy_jpunit(median_val)}")
    
    if target_amount:
        fig.add_vline(x=target_amount, line_dash="solid", line_color="red",
                      annotation_text=f"目標: {format_jpy_jpunit(target_amount)}")
    
    fig.update_layout(
        title="シミュレーション終了時の資産額分布",
        xaxis_title="資産額",
        yaxis_title="頻度",
        height=400
    )
    
    # Use Japanese format for X-axis
    fig.update_xaxes(
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_summary_metrics(
    simulations: np.ndarray,
    percentiles: Dict[str, np.ndarray],
    life_events: List[Dict],
    retirement_plan: Dict
):
    """Render summary metrics."""
    st.markdown("### シミュレーション結果サマリー")
    
    final_values = simulations[:, -1]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "期待最終資産（平均）",
            format_jpy_jpunit(np.mean(final_values))
        )
    
    with col2:
        st.metric(
            "最終資産（中央値）",
            format_jpy_jpunit(np.median(final_values))
        )
    
    with col3:
        st.metric(
            "最終資産（5%タイル）",
            format_jpy_jpunit(np.percentile(final_values, 5)),
            help="悲観的シナリオ（下位5%）"
        )
    
    with col4:
        st.metric(
            "最終資産（95%タイル）",
            format_jpy_jpunit(np.percentile(final_values, 95)),
            help="楽観的シナリオ（上位5%）"
        )
    
    st.markdown("---")
    
    st.markdown("#### 詳細統計")
    
    total_events_cost = sum(event['target_amount'] for event in life_events)
    
    stats_data = {
        '項目': [
            '初期資産',
            'ライフイベント総額',
            '最終資産（平均）',
            '最終資産（標準偏差）',
            '資産枯渇確率',
            '目標達成確率（1億円以上）'
        ],
        '値': [
            format_jpy_jpunit(simulations[0, 0]),
            format_jpy_jpunit(total_events_cost),
            format_jpy_jpunit(np.mean(final_values)),
            format_jpy_jpunit(np.std(final_values)),
            f"{(final_values <= 0).sum() / len(final_values) * 100:.1f}%",
            f"{(final_values >= 100000000).sum() / len(final_values) * 100:.1f}%"
        ]
    }
    
    st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)


def render_yearly_projection_table(
    years_array: np.ndarray,
    percentiles: Dict[str, np.ndarray],
    current_age: int
):
    """Render yearly projection table."""
    st.markdown("### 年次資産推移（数値）")
    
    current_year = datetime.now().year
    
    step = max(1, len(years_array) // 10)
    selected_years = list(range(0, len(years_array), step))
    if len(years_array) - 1 not in selected_years:
        selected_years.append(len(years_array) - 1)
    
    table_data = []
    for i in selected_years:
        table_data.append({
            '年': current_year + years_array[i],
            '年齢': f"{current_age + years_array[i]}歳",
            '5%タイル': format_jpy_jpunit(percentiles['p5'][i]),
            '25%タイル': format_jpy_jpunit(percentiles['p25'][i]),
            '中央値': format_jpy_jpunit(percentiles['p50'][i]),
            '75%タイル': format_jpy_jpunit(percentiles['p75'][i]),
            '95%タイル': format_jpy_jpunit(percentiles['p95'][i])
        })
    
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)


def check_profile_completeness():
    """Check if user profile is complete enough for simulation."""
    profile = st.session_state.user_profile
    
    issues = []
    
    if profile['cashflow']['annual_income'] == 0:
        issues.append("年間収入が設定されていません")
    
    if profile['cashflow']['monthly_investment'] == 0:
        issues.append("毎月の投資可能額が設定されていません")
    
    if profile['assets']['savings'] == 0:
        issues.append("預貯金総額が設定されていません")
    
    return issues


def main():
    """Main page entry point."""
    initialize_simulation_session_state()
    
    st.title("資産シミュレーション")
    st.markdown("ユーザープロファイルとライフイベントに基づく資産推移シミュレーション")
    
    st.page_link("app.py", label="ポートフォリオ入力に戻る", icon="🏠")
    
    st.markdown("---")
    
    issues = check_profile_completeness()
    if issues:
        st.warning("シミュレーションを実行するには、以下の情報を入力してください:")
        for issue in issues:
            st.write(f"- {issue}")
        st.page_link(
            "pages/03_ユーザープロファイル.py",
            label="プロファイルを編集",
            icon="👤"
        )
        st.stop()
    
    profile = st.session_state.user_profile
    life_events = st.session_state.life_events
    retirement = st.session_state.retirement_plan
    
    st.markdown("### 現在の設定")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**プロファイル**")
        st.write(f"年齢: {profile['personal']['age']}歳")
        st.write(f"年間収入: ¥{profile['cashflow']['annual_income']:,}")
        st.write(f"月間投資額: ¥{profile['cashflow']['monthly_investment']:,}")
    
    with col2:
        st.markdown("**資産**")
        st.write(f"預貯金: ¥{profile['assets']['savings']:,}")
        total_debt = sum(loan['balance'] for loan in profile['liabilities'])
        st.write(f"負債: ¥{total_debt:,}")
    
    with col3:
        st.markdown("**リタイアメント**")
        st.write(f"目標年齢: {retirement['target_age']}歳")
        st.write(f"年間生活費: ¥{retirement['annual_expense']:,}")
        st.write(f"ライフイベント: {len(life_events)}件")
    
    st.markdown("---")
    
    expected_return, volatility, num_simulations = render_simulation_settings()
    
    st.markdown("---")
    
    if st.button("シミュレーション実行", type="primary"):
        with st.spinner("シミュレーション実行中..."):
            current_age = profile['personal']['age']
            initial_assets = profile['assets']['savings']
            annual_investment = profile['cashflow']['monthly_investment'] * 12
            retirement_age = retirement['target_age']
            retirement_expense = retirement['annual_expense']
            
            simulation_years = max(retirement_age - current_age + 20, 30)
            
            years_array, simulations = run_asset_simulation(
                initial_assets=initial_assets,
                annual_investment=annual_investment,
                expected_return=expected_return,
                volatility=volatility,
                years=simulation_years,
                life_events=life_events,
                retirement_age=retirement_age,
                current_age=current_age,
                retirement_expense=retirement_expense,
                num_simulations=num_simulations
            )
            
            percentiles = calculate_percentiles(simulations)
            
            st.session_state.simulation_results = {
                'years_array': years_array,
                'simulations': simulations,
                'percentiles': percentiles
            }
        
        st.success("シミュレーション完了")
    
    if 'simulation_results' in st.session_state:
        results = st.session_state.simulation_results
        
        render_asset_projection_chart(
            results['years_array'],
            results['percentiles'],
            life_events,
            retirement['target_age'],
            profile['personal']['age']
        )
        
        render_final_value_histogram(results['simulations'])
        
        render_summary_metrics(
            results['simulations'],
            results['percentiles'],
            life_events,
            retirement
        )
        
        with st.expander("年次資産推移（数値表）", expanded=False):
            render_yearly_projection_table(
                results['years_array'],
                results['percentiles'],
                profile['personal']['age']
            )
    
    st.markdown("---")
    
    st.markdown("### 関連ページ")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link(
            "pages/03_ユーザープロファイル.py",
            label="プロファイル編集",
            icon="👤"
        )
    with col2:
        st.page_link(
            "pages/04_ライフイベント計画.py",
            label="ライフイベント編集",
            icon="📅"
        )
    with col3:
        st.page_link(
            "pages/01_現在ポートフォリオ分析.py",
            label="ポートフォリオ分析",
            icon="📈"
        )


if __name__ == "__main__":
    main()
