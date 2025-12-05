"""
Current Portfolio Analysis Page
Displays analysis results for the current portfolio holdings.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from data_fetcher import (
    prepare_analysis_data,
    create_returns_matrix,
    get_fund_list
)
from ui_components import render_full_analysis

# Page configuration
st.set_page_config(
    page_title="現在ポートフォリオ分析",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def initialize_session_state():
    """Initialize session state variables if not present."""
    if 'current_portfolio' not in st.session_state:
        st.session_state.current_portfolio = {}
    if 'start_date' not in st.session_state:
        st.session_state.start_date = datetime(2019, 1, 1)
    if 'end_date' not in st.session_state:
        st.session_state.end_date = datetime(2024, 12, 31)
    if 'mc_simulations' not in st.session_state:
        st.session_state.mc_simulations = 5000
    if 'mc_horizon' not in st.session_state:
        st.session_state.mc_horizon = 252


def main():
    """Main page entry point."""
    initialize_session_state()
    
    st.title("現在のポートフォリオ分析")
    st.markdown("現在保有しているポートフォリオの詳細分析")
    
    # Navigation back to input page
    st.page_link("app.py", label="入力ページに戻る", icon="🏠")
    
    st.markdown("---")
    
    # Check if portfolio is set
    if not st.session_state.current_portfolio:
        st.warning("現在のポートフォリオが設定されていません。入力ページでポートフォリオを設定してください。")
        st.page_link("app.py", label="入力ページへ移動", icon="📝")
        return
    
    # Display analysis period info
    st.info(f"分析期間: {st.session_state.start_date.strftime('%Y-%m-%d')} 〜 {st.session_state.end_date.strftime('%Y-%m-%d')}")
    
    # Fetch and prepare data
    portfolio = st.session_state.current_portfolio
    fund_ids = list(portfolio.keys())
    
    with st.spinner("データを取得・処理中..."):
        processed_data = prepare_analysis_data(
            fund_ids,
            st.session_state.start_date,
            st.session_state.end_date
        )
        returns_matrix = create_returns_matrix(processed_data, fund_ids)
    
    if returns_matrix.empty:
        st.error("選択された期間のデータが取得できませんでした。")
        return
    
    # Render full analysis
    render_full_analysis(
        processed_data=processed_data,
        returns_matrix=returns_matrix,
        portfolio=portfolio,
        portfolio_name="現在のポートフォリオ",
        mc_simulations=st.session_state.mc_simulations,
        mc_horizon=st.session_state.mc_horizon
    )


if __name__ == "__main__":
    main()
