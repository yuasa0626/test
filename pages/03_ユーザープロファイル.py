"""
User Profile Input Page
Collects user and family information, cashflow, assets, and liabilities.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.formatters import format_jpy_plain, format_jpy_jpunit

# Page configuration
st.set_page_config(
    page_title="ユーザープロファイル",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS to hide number input spinners for cleaner UI
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


def initialize_profile_session_state():
    """Initialize session state for user profile."""
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {
            'personal': {
                'age': 30,
                'occupation': '会社員'
            },
            'family': {
                'has_spouse': False,
                'spouse_age': None,
                'children': []
            },
            'cashflow': {
                'annual_income': 0,
                'annual_expense': 0,
                'monthly_investment': 0
            },
            'assets': {
                'savings': 0,
                'emergency_fund': 0
            },
            'liabilities': []
        }
    if 'life_events' not in st.session_state:
        st.session_state.life_events = []
    if 'retirement_plan' not in st.session_state:
        st.session_state.retirement_plan = {
            'target_age': 65,
            'annual_expense': 3000000
        }


def render_personal_info_form():
    """Render personal information form."""
    st.markdown("### 本人情報")
    
    profile = st.session_state.user_profile
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input(
            "年齢",
            min_value=18,
            max_value=100,
            value=profile['personal']['age'],
            step=1,
            key="personal_age"
        )
    
    with col2:
        occupation_options = [
            '会社員', '公務員', '自営業', 'フリーランス', 
            'パート・アルバイト', '専業主婦/主夫', '学生', '無職', 'その他'
        ]
        occupation = st.selectbox(
            "職業",
            options=occupation_options,
            index=occupation_options.index(profile['personal']['occupation']) 
                if profile['personal']['occupation'] in occupation_options else 0,
            key="personal_occupation"
        )
    
    return {'age': age, 'occupation': occupation}


def render_family_info_form():
    """Render family information form."""
    st.markdown("### 家族情報")
    
    profile = st.session_state.user_profile
    
    col1, col2 = st.columns(2)
    
    with col1:
        has_spouse = st.checkbox(
            "配偶者あり",
            value=profile['family']['has_spouse'],
            key="has_spouse"
        )
        
        spouse_age = None
        if has_spouse:
            spouse_age = st.number_input(
                "配偶者の年齢",
                min_value=18,
                max_value=100,
                value=profile['family']['spouse_age'] or 30,
                step=1,
                key="spouse_age"
            )
    
    with col2:
        num_children = st.number_input(
            "子供の人数",
            min_value=0,
            max_value=10,
            value=len(profile['family']['children']),
            step=1,
            key="num_children"
        )
    
    children = []
    if num_children > 0:
        st.markdown("**子供の年齢**")
        cols = st.columns(min(num_children, 4))
        for i in range(num_children):
            with cols[i % 4]:
                default_age = profile['family']['children'][i] if i < len(profile['family']['children']) else 0
                child_age = st.number_input(
                    f"子供{i+1}",
                    min_value=0,
                    max_value=50,
                    value=default_age,
                    step=1,
                    key=f"child_age_{i}"
                )
                children.append(child_age)
    
    return {
        'has_spouse': has_spouse,
        'spouse_age': spouse_age,
        'children': children
    }


def render_cashflow_form():
    """Render cashflow information form."""
    st.markdown("### キャッシュフロー")
    
    profile = st.session_state.user_profile
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        annual_income = st.number_input(
            "世帯年間手取り収入 (円)",
            min_value=0,
            value=profile['cashflow']['annual_income'],
            step=100000,
            format="%d",
            key="annual_income",
            help="税引後の手取り収入"
        )
    
    with col2:
        annual_expense = st.number_input(
            "年間支出総額 (円)",
            min_value=0,
            value=profile['cashflow']['annual_expense'],
            step=100000,
            format="%d",
            key="annual_expense"
        )
    
    with col3:
        monthly_investment = st.number_input(
            "毎月の投資可能額 (円)",
            min_value=0,
            value=profile['cashflow']['monthly_investment'],
            step=10000,
            format="%d",
            key="monthly_investment"
        )
    
    return {
        'annual_income': annual_income,
        'annual_expense': annual_expense,
        'monthly_investment': monthly_investment
    }


def render_assets_form():
    """Render assets information form."""
    st.markdown("### 資産")
    
    profile = st.session_state.user_profile
    
    col1, col2 = st.columns(2)
    
    with col1:
        savings = st.number_input(
            "預貯金総額 (円)",
            min_value=0,
            value=profile['assets']['savings'],
            step=100000,
            format="%d",
            key="savings"
        )
    
    with col2:
        emergency_fund = st.number_input(
            "緊急予備資金 (円)",
            min_value=0,
            value=profile['assets']['emergency_fund'],
            step=100000,
            format="%d",
            key="emergency_fund",
            help="生活費の3〜6ヶ月分が目安"
        )
    
    return {
        'savings': savings,
        'emergency_fund': emergency_fund
    }


def render_liabilities_form():
    """Render liabilities information form."""
    st.markdown("### 負債")
    
    profile = st.session_state.user_profile
    
    loan_types = ['住宅ローン', '自動車ローン', '教育ローン', 'その他']
    
    num_loans = st.number_input(
        "ローンの件数",
        min_value=0,
        max_value=10,
        value=len(profile['liabilities']),
        step=1,
        key="num_loans"
    )
    
    liabilities = []
    if num_loans > 0:
        for i in range(num_loans):
            st.markdown(f"**ローン {i+1}**")
            
            default_loan = profile['liabilities'][i] if i < len(profile['liabilities']) else {
                'type': '住宅ローン',
                'balance': 0,
                'interest_rate': 1.0,
                'monthly_payment': 0
            }
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                loan_type = st.selectbox(
                    "種別",
                    options=loan_types,
                    index=loan_types.index(default_loan['type']) if default_loan['type'] in loan_types else 0,
                    key=f"loan_type_{i}"
                )
            
            with col2:
                balance = st.number_input(
                    "残高 (円)",
                    min_value=0,
                    value=default_loan['balance'],
                    step=100000,
                    format="%d",
                    key=f"loan_balance_{i}"
                )
            
            with col3:
                interest_rate = st.number_input(
                    "金利 (%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=float(default_loan['interest_rate']),
                    step=0.1,
                    format="%.2f",
                    key=f"loan_rate_{i}"
                )
            
            with col4:
                monthly_payment = st.number_input(
                    "月返済額 (円)",
                    min_value=0,
                    value=default_loan['monthly_payment'],
                    step=10000,
                    format="%d",
                    key=f"loan_payment_{i}"
                )
            
            liabilities.append({
                'type': loan_type,
                'balance': balance,
                'interest_rate': interest_rate,
                'monthly_payment': monthly_payment
            })
    
    return liabilities


def render_profile_summary():
    """Render profile summary."""
    st.markdown("### プロファイル概要")
    
    profile = st.session_state.user_profile
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**本人・家族**")
        st.write(f"年齢: {profile['personal']['age']}歳")
        st.write(f"職業: {profile['personal']['occupation']}")
        if profile['family']['has_spouse']:
            st.write(f"配偶者: {profile['family']['spouse_age']}歳")
        if profile['family']['children']:
            children_str = ', '.join([f"{age}歳" for age in profile['family']['children']])
            st.write(f"子供: {children_str}")
    
    with col2:
        st.markdown("**キャッシュフロー**")
        st.write(f"年間収入: {format_jpy_jpunit(profile['cashflow']['annual_income'])}")
        st.write(f"年間支出: {format_jpy_jpunit(profile['cashflow']['annual_expense'])}")
        st.write(f"月間投資可能額: {format_jpy_jpunit(profile['cashflow']['monthly_investment'])}")
        annual_savings = profile['cashflow']['annual_income'] - profile['cashflow']['annual_expense']
        st.write(f"年間貯蓄可能額: {format_jpy_jpunit(annual_savings)}")
    
    with col3:
        st.markdown("**資産・負債**")
        st.write(f"預貯金: {format_jpy_jpunit(profile['assets']['savings'])}")
        st.write(f"緊急予備資金: {format_jpy_jpunit(profile['assets']['emergency_fund'])}")
        total_debt = sum(loan['balance'] for loan in profile['liabilities'])
        st.write(f"負債総額: {format_jpy_jpunit(total_debt)}")
        net_assets = profile['assets']['savings'] - total_debt
        st.write(f"純資産: {format_jpy_jpunit(net_assets)}")


def main():
    """Main page entry point."""
    initialize_profile_session_state()
    
    st.title("ユーザープロファイル")
    st.markdown("家族情報、収支、資産・負債を入力してください")
    
    # Navigation
    st.page_link("app.py", label="ポートフォリオ入力に戻る", icon="🏠")
    
    st.markdown("---")
    
    with st.form(key="profile_form"):
        # Personal info
        personal_data = render_personal_info_form()
        
        st.markdown("---")
        
        # Family info
        family_data = render_family_info_form()
        
        st.markdown("---")
        
        # Cashflow
        cashflow_data = render_cashflow_form()
        
        st.markdown("---")
        
        # Assets
        assets_data = render_assets_form()
        
        st.markdown("---")
        
        # Liabilities
        liabilities_data = render_liabilities_form()
        
        st.markdown("---")
        
        # Submit button
        submitted = st.form_submit_button("プロファイルを保存", type="primary")
        
        if submitted:
            st.session_state.user_profile = {
                'personal': personal_data,
                'family': family_data,
                'cashflow': cashflow_data,
                'assets': assets_data,
                'liabilities': liabilities_data
            }
            st.success("プロファイルを保存しました")
    
    st.markdown("---")
    
    # Profile summary
    render_profile_summary()
    
    st.markdown("---")
    
    # Navigation to next step
    st.markdown("### 次のステップ")
    col1, col2 = st.columns(2)
    with col1:
        st.page_link(
            "pages/04_ライフイベント計画.py",
            label="ライフイベント・リタイアメント計画へ",
            icon="📅"
        )
    with col2:
        st.page_link(
            "pages/05_資産シミュレーション.py",
            label="資産シミュレーションへ",
            icon="📊"
        )


if __name__ == "__main__":
    main()
