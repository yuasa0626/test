"""
Investment Trust Portfolio Analysis Tool - Input Page
Main entry point for portfolio data input.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict

from data_fetcher import (
    get_fund_list,
    get_fund_info,
    get_crisis_period,
    FUND_DEFINITIONS
)

# Page configuration
st.set_page_config(
    page_title="投資信託ポートフォリオ分析ツール - 入力",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: #f0f2f6;
        border-radius: 5px;
    }
    .fund-card {
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .stForm {
        background-color: #fafafa;
        padding: 1.5rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'current_portfolio' not in st.session_state:
        st.session_state.current_portfolio = {}
    if 'proposed_portfolio' not in st.session_state:
        st.session_state.proposed_portfolio = {}
    if 'start_date' not in st.session_state:
        st.session_state.start_date = datetime(2019, 1, 1)
    if 'end_date' not in st.session_state:
        st.session_state.end_date = datetime(2024, 12, 31)
    if 'mc_simulations' not in st.session_state:
        st.session_state.mc_simulations = 5000
    if 'mc_horizon' not in st.session_state:
        st.session_state.mc_horizon = 252
    if 'input_submitted' not in st.session_state:
        st.session_state.input_submitted = False


def render_fund_table():
    """Render available funds table."""
    st.subheader("利用可能なファンド一覧")
    
    fund_data = []
    for fund_id, info in FUND_DEFINITIONS.items():
        fund_data.append({
            "ファンドID": fund_id,
            "ファンド名": info['name'],
            "カテゴリ": info['category'],
            "期待リターン": f"{info['base_return']*100:.1f}%",
            "ボラティリティ": f"{info['volatility']*100:.1f}%"
        })
    
    st.dataframe(pd.DataFrame(fund_data), use_container_width=True, hide_index=True)


def render_portfolio_input_form(form_key: str, portfolio_name: str, session_key: str):
    """Render portfolio input form."""
    fund_list = get_fund_list()
    fund_options = list(fund_list.keys())
    
    st.markdown(f"### {portfolio_name}")
    
    with st.form(key=form_key):
        # Fund selection
        selected_funds = st.multiselect(
            "ファンドを選択",
            options=fund_options,
            format_func=lambda x: f"{x}: {fund_list[x]}",
            key=f"{form_key}_funds",
            default=list(st.session_state.get(session_key, {}).keys())
        )
        
        # Amount inputs for selected funds
        amounts = {}
        if selected_funds:
            st.markdown("**保有金額を入力 (JPY):**")
            cols = st.columns(2)
            for i, fund_id in enumerate(selected_funds):
                with cols[i % 2]:
                    default_val = st.session_state.get(session_key, {}).get(fund_id, 100000)
                    amount = st.number_input(
                        f"{fund_id}: {fund_list[fund_id][:30]}...",
                        min_value=0,
                        value=default_val,
                        step=10000,
                        key=f"{form_key}_amount_{fund_id}"
                    )
                    if amount > 0:
                        amounts[fund_id] = amount
        
        submitted = st.form_submit_button(f"{portfolio_name}を保存", type="primary")
        
        if submitted:
            st.session_state[session_key] = amounts
            st.success(f"{portfolio_name}を保存しました")
            return True
    
    return False


def render_analysis_settings_form():
    """Render analysis settings form."""
    st.markdown("### 分析設定")
    
    with st.form(key="settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**分析期間**")
            
            period_option = st.radio(
                "期間タイプ",
                options=['カスタム', '危機時期間 (COVID-19)'],
                key="period_type"
            )
            
            if period_option == '危機時期間 (COVID-19)':
                crisis = get_crisis_period()
                start_date = crisis['start']
                end_date = crisis['end']
                st.info(f"危機時期間: {crisis['start'].strftime('%Y-%m-%d')} 〜 {crisis['end'].strftime('%Y-%m-%d')}")
            else:
                start_date = st.date_input(
                    "開始日",
                    value=st.session_state.start_date,
                    min_value=datetime(2015, 1, 1),
                    max_value=datetime(2024, 12, 31),
                    key="start_date_input"
                )
                end_date = st.date_input(
                    "終了日",
                    value=st.session_state.end_date,
                    min_value=datetime(2015, 1, 1),
                    max_value=datetime(2024, 12, 31),
                    key="end_date_input"
                )
        
        with col2:
            st.markdown("**モンテカルロ・シミュレーション設定**")
            
            mc_simulations = st.slider(
                "シミュレーション回数",
                min_value=1000,
                max_value=10000,
                value=st.session_state.mc_simulations,
                step=1000,
                key="mc_sim_slider"
            )
            
            mc_horizon = st.slider(
                "予測期間 (営業日)",
                min_value=63,
                max_value=756,
                value=st.session_state.mc_horizon,
                step=63,
                key="mc_horizon_slider",
                help="63日=約3ヶ月, 252日=約1年, 756日=約3年"
            )
        
        submitted = st.form_submit_button("設定を保存", type="primary")
        
        if submitted:
            if isinstance(start_date, datetime):
                st.session_state.start_date = start_date
            else:
                st.session_state.start_date = datetime.combine(start_date, datetime.min.time())
            
            if isinstance(end_date, datetime):
                st.session_state.end_date = end_date
            else:
                st.session_state.end_date = datetime.combine(end_date, datetime.min.time())
            
            st.session_state.mc_simulations = mc_simulations
            st.session_state.mc_horizon = mc_horizon
            st.success("設定を保存しました")
            return True
    
    return False


def render_current_settings():
    """Display current settings summary."""
    st.markdown("### 現在の設定")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**現在のポートフォリオ**")
        if st.session_state.current_portfolio:
            total = sum(st.session_state.current_portfolio.values())
            st.write(f"合計: ¥{total:,.0f}")
            st.write(f"ファンド数: {len(st.session_state.current_portfolio)}")
            for fund_id, amount in st.session_state.current_portfolio.items():
                st.write(f"- {fund_id}: ¥{amount:,.0f}")
        else:
            st.info("未設定")
    
    with col2:
        st.markdown("**検討中のポートフォリオ**")
        if st.session_state.proposed_portfolio:
            total = sum(st.session_state.proposed_portfolio.values())
            st.write(f"合計: ¥{total:,.0f}")
            st.write(f"ファンド数: {len(st.session_state.proposed_portfolio)}")
            for fund_id, amount in st.session_state.proposed_portfolio.items():
                st.write(f"- {fund_id}: ¥{amount:,.0f}")
        else:
            st.info("未設定")
    
    with col3:
        st.markdown("**分析設定**")
        st.write(f"期間: {st.session_state.start_date.strftime('%Y-%m-%d')} 〜 {st.session_state.end_date.strftime('%Y-%m-%d')}")
        st.write(f"シミュレーション回数: {st.session_state.mc_simulations:,}")
        st.write(f"予測期間: {st.session_state.mc_horizon}営業日")


def render_navigation():
    """Render navigation to analysis pages."""
    st.markdown("---")
    st.markdown("### 分析ページへ移動")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.current_portfolio:
            st.page_link(
                "pages/01_現在ポートフォリオ分析.py",
                label="現在のポートフォリオ分析を見る",
                icon="📈"
            )
        else:
            st.info("現在のポートフォリオを入力してください")
    
    with col2:
        if st.session_state.proposed_portfolio:
            st.page_link(
                "pages/02_入れ替え後ポートフォリオ分析.py",
                label="入れ替え後のポートフォリオ分析を見る",
                icon="📊"
            )
        else:
            st.info("検討中のポートフォリオを入力してください")
    
    st.markdown("---")
    st.markdown("### 資産計画")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.page_link(
            "pages/03_ユーザープロファイル.py",
            label="ユーザープロファイル",
            icon="👤"
        )
    
    with col2:
        st.page_link(
            "pages/04_ライフイベント計画.py",
            label="ライフイベント計画",
            icon="📅"
        )
    
    with col3:
        st.page_link(
            "pages/05_資産シミュレーション.py",
            label="資産シミュレーション",
            icon="📊"
        )


def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Header
    st.title("投資信託ポートフォリオ分析ツール")
    st.markdown("高度なポートフォリオ分析とモンテカルロ・シミュレーション")
    
    st.markdown("---")
    
    # Available funds table
    with st.expander("利用可能なファンド一覧を表示", expanded=False):
        render_fund_table()
    
    st.markdown("---")
    
    # Portfolio input forms
    col1, col2 = st.columns(2)
    
    with col1:
        render_portfolio_input_form(
            "current_portfolio_form",
            "現在のポートフォリオ",
            "current_portfolio"
        )
    
    with col2:
        render_portfolio_input_form(
            "proposed_portfolio_form",
            "検討中のポートフォリオ",
            "proposed_portfolio"
        )
    
    st.markdown("---")
    
    # Analysis settings
    render_analysis_settings_form()
    
    st.markdown("---")
    
    # Current settings summary
    render_current_settings()
    
    # Navigation to analysis pages
    render_navigation()


if __name__ == "__main__":
    main()
