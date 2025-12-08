"""
Life Event and Retirement Planning Page (Enhanced)
Allows users to register life events with card-style inputs for education, housing, vehicles, and travel.
Includes automatic cost calculations based on government statistics and typical costs.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List
import sys
import os
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.formatters import format_jpy_plain, format_jpy_jpunit, format_jpy_axis, get_axis_tickvals_ticktext
from models.education_cost import (
    EDUCATION_PATHS, get_education_path_names, get_education_summary,
    generate_education_cashflow, estimate_remaining_education_cost
)
from models.housing_cost import (
    HOUSING_TYPES, suggest_renovations, calculate_total_housing_cost,
    get_housing_cashflow
)
from models.vehicle_cost import (
    VEHICLE_TYPES, REPLACEMENT_CYCLES, get_vehicle_type_names,
    get_replacement_cycle_names, calculate_annual_running_cost,
    calculate_vehicle_cashflow, get_vehicle_summary
)
from models.travel_cost import (
    TRAVEL_TYPES, TRAVEL_FREQUENCIES, get_travel_type_names,
    get_frequency_names, calculate_annual_travel_cost, get_travel_summary
)

# Page configuration
st.set_page_config(
    page_title="ライフイベント・リタイアメント計画",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS to hide number input spinners and style cards
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


def initialize_life_event_session_state():
    """Initialize session state for life events."""
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
    if 'education_plans' not in st.session_state:
        st.session_state.education_plans = []
    if 'housing_plan' not in st.session_state:
        st.session_state.housing_plan = {
            'housing_type': 'rental',
            'building_age': 0,
            'monthly_rent': 100000,
            'loan_balance': 0,
            'loan_rate': 0.01,
            'loan_monthly_payment': 0,
            'loan_remaining_years': 0,
            'planned_purchase': False,
            'purchase_years_from_now': 5,
            'purchase_amount': 40000000,
        }
    if 'vehicle_plans' not in st.session_state:
        st.session_state.vehicle_plans = []
    if 'travel_plans' not in st.session_state:
        st.session_state.travel_plans = []
    if 'retirement_plan' not in st.session_state:
        st.session_state.retirement_plan = {
            'target_age': 65,
            'annual_expense': 3000000,
            'continue_investing': True
        }


def render_education_cards():
    """Render education planning cards for each child."""
    st.markdown("### 教育費計画")
    st.markdown("子供ごとに教育コースを選択してください（文科省統計データに基づく自動計算）")
    
    children = st.session_state.user_profile['family'].get('children', [])
    
    if not children:
        st.info("子供の情報が登録されていません。プロファイルページで登録してください。")
        return []
    
    education_plans = []
    path_names = get_education_path_names()
    path_options = list(path_names.keys())
    
    for i, child_age in enumerate(children):
        with st.expander(f"子供{i+1}（{child_age}歳）の教育計画", expanded=True):
            default_plan = st.session_state.education_plans[i] if i < len(st.session_state.education_plans) else {
                'path_id': 'public_to_private_univ',
                'living_away': False
            }
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                path_id = st.selectbox(
                    "教育コース",
                    options=path_options,
                    format_func=lambda x: path_names[x],
                    index=path_options.index(default_plan['path_id']) if default_plan['path_id'] in path_options else 0,
                    key=f"edu_path_{i}",
                    help="選択したコースに基づいて教育費を自動計算します"
                )
            
            with col2:
                living_away = st.checkbox(
                    "大学で一人暮らし",
                    value=default_plan.get('living_away', False),
                    key=f"edu_living_{i}",
                    help="大学進学時に下宿・一人暮らしをする場合"
                )
            
            # Show cost summary
            summary = get_education_summary(path_id, living_away)
            remaining_cost = estimate_remaining_education_cost(child_age, path_id, living_away)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総教育費（全期間）", format_jpy_jpunit(summary['total_cost']))
            with col2:
                st.metric("残り教育費", format_jpy_jpunit(remaining_cost))
            with col3:
                st.caption(summary['note'])
            
            # Show breakdown
            with st.expander("費用内訳"):
                breakdown_data = [
                    {'段階': stage, '費用': format_jpy_jpunit(cost)}
                    for stage, cost in summary['breakdown'].items()
                ]
                st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)
            
            education_plans.append({
                'child_index': i,
                'child_age': child_age,
                'path_id': path_id,
                'living_away': living_away,
                'total_cost': summary['total_cost'],
                'remaining_cost': remaining_cost
            })
    
    return education_plans


def render_housing_card():
    """Render housing planning card."""
    st.markdown("### 住宅計画")
    
    housing = st.session_state.housing_plan
    
    col1, col2 = st.columns(2)
    
    with col1:
        housing_type = st.selectbox(
            "住居形態",
            options=list(HOUSING_TYPES.keys()),
            format_func=lambda x: HOUSING_TYPES[x],
            index=list(HOUSING_TYPES.keys()).index(housing['housing_type']) if housing['housing_type'] in HOUSING_TYPES else 0,
            key="housing_type"
        )
    
    with col2:
        if housing_type != 'rental':
            building_age = st.number_input(
                "築年数",
                min_value=0,
                max_value=100,
                value=housing.get('building_age', 0),
                step=1,
                key="building_age"
            )
        else:
            building_age = 0
    
    # Rental specific
    monthly_rent = 0
    if housing_type == 'rental':
        monthly_rent = st.number_input(
            "月額家賃（円）",
            min_value=0,
            value=housing.get('monthly_rent', 100000),
            step=10000,
            format="%d",
            key="monthly_rent"
        )
    
    # Loan information for owned properties
    loan_balance = 0
    loan_rate = 0.01
    loan_monthly_payment = 0
    loan_remaining_years = 0
    
    if housing_type != 'rental':
        st.markdown("**住宅ローン情報**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            loan_balance = st.number_input(
                "ローン残高（円）",
                min_value=0,
                value=housing.get('loan_balance', 0),
                step=1000000,
                format="%d",
                key="loan_balance"
            )
        
        with col2:
            loan_rate = st.number_input(
                "金利（%）",
                min_value=0.0,
                max_value=10.0,
                value=float(housing.get('loan_rate', 0.01)) * 100,
                step=0.1,
                format="%.2f",
                key="loan_rate"
            ) / 100
        
        with col3:
            loan_monthly_payment = st.number_input(
                "月返済額（円）",
                min_value=0,
                value=housing.get('loan_monthly_payment', 0),
                step=10000,
                format="%d",
                key="loan_monthly_payment"
            )
        
        with col4:
            loan_remaining_years = st.number_input(
                "残り返済年数",
                min_value=0,
                max_value=50,
                value=housing.get('loan_remaining_years', 0),
                step=1,
                key="loan_remaining_years"
            )
    
    # Future purchase plan
    planned_purchase = False
    purchase_years_from_now = 5
    purchase_amount = 40000000
    
    if housing_type == 'rental':
        st.markdown("**住宅購入計画**")
        planned_purchase = st.checkbox(
            "住宅購入を予定している",
            value=housing.get('planned_purchase', False),
            key="planned_purchase"
        )
        
        if planned_purchase:
            col1, col2 = st.columns(2)
            with col1:
                purchase_years_from_now = st.number_input(
                    "購入予定（年後）",
                    min_value=1,
                    max_value=30,
                    value=housing.get('purchase_years_from_now', 5),
                    step=1,
                    key="purchase_years_from_now"
                )
            with col2:
                purchase_amount = st.number_input(
                    "購入予算（円）",
                    min_value=0,
                    value=housing.get('purchase_amount', 40000000),
                    step=1000000,
                    format="%d",
                    key="purchase_amount"
                )
    
    # Show renovation suggestions for owned properties
    if housing_type != 'rental' and building_age > 0:
        st.markdown("**リフォーム予測**")
        renovations = suggest_renovations(housing_type, building_age, years_to_simulate=20)
        if renovations:
            reno_data = [
                {
                    '項目': r['name'],
                    '時期': f"{r['years_from_now']}年後",
                    '築年数': f"{r['building_age_at_renovation']}年",
                    '費用目安': format_jpy_jpunit(r['cost_estimate'])
                }
                for r in renovations[:5]  # Show first 5
            ]
            st.dataframe(pd.DataFrame(reno_data), use_container_width=True, hide_index=True)
            st.caption("※築年数に基づく一般的なリフォーム時期の目安です")
    
    return {
        'housing_type': housing_type,
        'building_age': building_age,
        'monthly_rent': monthly_rent,
        'loan_balance': loan_balance,
        'loan_rate': loan_rate,
        'loan_monthly_payment': loan_monthly_payment,
        'loan_remaining_years': loan_remaining_years,
        'planned_purchase': planned_purchase,
        'purchase_years_from_now': purchase_years_from_now,
        'purchase_amount': purchase_amount,
    }


def render_vehicle_cards():
    """Render vehicle planning cards."""
    st.markdown("### 車両計画")
    
    vehicle_type_names = get_vehicle_type_names()
    cycle_names = get_replacement_cycle_names()
    
    num_vehicles = st.number_input(
        "保有車両数",
        min_value=0,
        max_value=5,
        value=len(st.session_state.vehicle_plans),
        step=1,
        key="num_vehicles"
    )
    
    vehicle_plans = []
    
    if num_vehicles > 0:
        for i in range(num_vehicles):
            with st.expander(f"車両{i+1}", expanded=True):
                default_vehicle = st.session_state.vehicle_plans[i] if i < len(st.session_state.vehicle_plans) else {
                    'vehicle_type': 'compact',
                    'purchase_price': 2000000,
                    'current_age': 0,
                    'replacement_cycle': 'medium',
                    'annual_distance': 10000
                }
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    vehicle_type = st.selectbox(
                        "車種",
                        options=list(vehicle_type_names.keys()),
                        format_func=lambda x: vehicle_type_names[x],
                        index=list(vehicle_type_names.keys()).index(default_vehicle['vehicle_type']) if default_vehicle['vehicle_type'] in vehicle_type_names else 0,
                        key=f"vehicle_type_{i}"
                    )
                
                with col2:
                    purchase_price = st.number_input(
                        "購入価格（円）",
                        min_value=0,
                        value=default_vehicle.get('purchase_price', 2000000),
                        step=100000,
                        format="%d",
                        key=f"vehicle_price_{i}"
                    )
                
                with col3:
                    current_age = st.number_input(
                        "現在の車齢（年）",
                        min_value=0,
                        max_value=30,
                        value=default_vehicle.get('current_age', 0),
                        step=1,
                        key=f"vehicle_age_{i}"
                    )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    replacement_cycle = st.selectbox(
                        "買替サイクル",
                        options=list(cycle_names.keys()),
                        format_func=lambda x: cycle_names[x],
                        index=list(cycle_names.keys()).index(default_vehicle['replacement_cycle']) if default_vehicle['replacement_cycle'] in cycle_names else 0,
                        key=f"vehicle_cycle_{i}"
                    )
                
                with col2:
                    annual_distance = st.number_input(
                        "年間走行距離（km）",
                        min_value=0,
                        max_value=50000,
                        value=default_vehicle.get('annual_distance', 10000),
                        step=1000,
                        key=f"vehicle_distance_{i}"
                    )
                
                # Show cost summary
                summary = get_vehicle_summary(vehicle_type, purchase_price, replacement_cycle, annual_distance)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("年間維持費", format_jpy_jpunit(summary['annual_running_cost']['total']))
                with col2:
                    st.metric("年間平均コスト", format_jpy_jpunit(summary['annual_average_cost']))
                with col3:
                    st.caption("※税金、保険、メンテナンス、燃料費を含む")
                
                vehicle_plans.append({
                    'vehicle_type': vehicle_type,
                    'purchase_price': purchase_price,
                    'current_age': current_age,
                    'replacement_cycle': replacement_cycle,
                    'annual_distance': annual_distance
                })
    
    return vehicle_plans


def render_travel_cards():
    """Render travel planning cards."""
    st.markdown("### 旅行計画")
    
    travel_type_names = get_travel_type_names()
    frequency_names = get_frequency_names()
    family_size = 1 + (1 if st.session_state.user_profile['family']['has_spouse'] else 0) + len(st.session_state.user_profile['family'].get('children', []))
    
    num_travel_plans = st.number_input(
        "旅行プラン数",
        min_value=0,
        max_value=5,
        value=len(st.session_state.travel_plans),
        step=1,
        key="num_travel_plans"
    )
    
    travel_plans = []
    
    if num_travel_plans > 0:
        for i in range(num_travel_plans):
            with st.expander(f"旅行プラン{i+1}", expanded=True):
                default_plan = st.session_state.travel_plans[i] if i < len(st.session_state.travel_plans) else {
                    'travel_type': 'domestic_short',
                    'frequency': 'annual',
                    'budget_per_trip': None,
                    'num_travelers': family_size
                }
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    travel_type = st.selectbox(
                        "旅行タイプ",
                        options=list(travel_type_names.keys()),
                        format_func=lambda x: travel_type_names[x],
                        index=list(travel_type_names.keys()).index(default_plan['travel_type']) if default_plan['travel_type'] in travel_type_names else 0,
                        key=f"travel_type_{i}"
                    )
                
                with col2:
                    frequency = st.selectbox(
                        "頻度",
                        options=list(frequency_names.keys()),
                        format_func=lambda x: frequency_names[x],
                        index=list(frequency_names.keys()).index(default_plan['frequency']) if default_plan['frequency'] in frequency_names else 0,
                        key=f"travel_freq_{i}"
                    )
                
                with col3:
                    num_travelers = st.number_input(
                        "人数",
                        min_value=1,
                        max_value=10,
                        value=default_plan.get('num_travelers', family_size),
                        step=1,
                        key=f"travel_num_{i}"
                    )
                
                # Budget input
                typical_cost = TRAVEL_TYPES[travel_type]['typical_cost']
                budget_per_trip = st.number_input(
                    f"1人あたり予算（円）※目安: {format_jpy_jpunit(typical_cost)}",
                    min_value=0,
                    value=default_plan.get('budget_per_trip') or typical_cost,
                    step=10000,
                    format="%d",
                    key=f"travel_budget_{i}"
                )
                
                # Show cost summary
                cost_info = calculate_annual_travel_cost(travel_type, frequency, budget_per_trip, num_travelers)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("1回あたり費用", format_jpy_jpunit(cost_info['cost_per_trip']))
                with col2:
                    st.metric("年間費用", format_jpy_jpunit(cost_info['annual_cost']))
                
                travel_plans.append({
                    'travel_type': travel_type,
                    'frequency': frequency,
                    'budget_per_trip': budget_per_trip,
                    'num_travelers': num_travelers
                })
    
    return travel_plans


def render_other_events_form():
    """Render form for other life events."""
    st.markdown("### その他のライフイベント")
    st.markdown("結婚、出産、その他の大型支出を登録してください")
    
    event_types = ['結婚', '出産', '大型家電購入', 'リフォーム', 'その他']
    
    other_events = [e for e in st.session_state.life_events if e.get('category') == 'other']
    
    num_events = st.number_input(
        "登録するイベント数",
        min_value=0,
        max_value=10,
        value=len(other_events),
        step=1,
        key="num_other_events"
    )
    
    events = []
    
    if num_events > 0:
        for i in range(num_events):
            with st.expander(f"イベント{i+1}", expanded=True):
                default_event = other_events[i] if i < len(other_events) else {
                    'type': '結婚',
                    'custom_name': '',
                    'years_from_now': 3,
                    'target_amount': 3000000
                }
                
                col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
                
                with col1:
                    event_type = st.selectbox(
                        "イベント種類",
                        options=event_types,
                        index=event_types.index(default_event['type']) if default_event['type'] in event_types else 0,
                        key=f"other_event_type_{i}"
                    )
                
                with col2:
                    custom_name = ""
                    if event_type == 'その他':
                        custom_name = st.text_input(
                            "イベント名",
                            value=default_event.get('custom_name', ''),
                            key=f"other_event_custom_{i}",
                            placeholder="イベント名を入力"
                        )
                    else:
                        st.text_input(
                            "イベント名",
                            value=event_type,
                            disabled=True,
                            key=f"other_event_name_display_{i}"
                        )
                
                with col3:
                    years_from_now = st.number_input(
                        "実現時期（年後）",
                        min_value=1,
                        max_value=50,
                        value=default_event['years_from_now'],
                        step=1,
                        key=f"other_event_years_{i}"
                    )
                
                with col4:
                    target_amount = st.number_input(
                        "目標金額（円）",
                        min_value=0,
                        value=default_event['target_amount'],
                        step=100000,
                        format="%d",
                        key=f"other_event_amount_{i}"
                    )
                
                events.append({
                    'category': 'other',
                    'type': event_type,
                    'custom_name': custom_name if event_type == 'その他' else '',
                    'years_from_now': years_from_now,
                    'target_amount': target_amount
                })
    
    return events


def render_retirement_plan_form():
    """Render retirement planning form."""
    st.markdown("### リタイアメント計画")
    
    retirement = st.session_state.retirement_plan
    current_age = st.session_state.user_profile['personal']['age']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        target_age = st.number_input(
            "希望リタイア年齢",
            min_value=current_age + 1,
            max_value=100,
            value=max(retirement['target_age'], current_age + 1),
            step=1,
            key="retirement_age"
        )
        years_to_retirement = target_age - current_age
        st.info(f"リタイアまで: {years_to_retirement}年")
    
    with col2:
        annual_expense = st.number_input(
            "リタイア後年間生活費（円）",
            min_value=0,
            value=retirement['annual_expense'],
            step=100000,
            format="%d",
            key="retirement_expense"
        )
    
    with col3:
        continue_investing = st.checkbox(
            "リタイア後も投資を継続",
            value=retirement.get('continue_investing', True),
            key="continue_investing",
            help="リタイア後も資産運用を継続するかどうか"
        )
    
    return {
        'target_age': target_age,
        'annual_expense': annual_expense,
        'continue_investing': continue_investing
    }


def render_comprehensive_summary():
    """Render comprehensive summary of all life events and costs."""
    st.markdown("### ライフプラン総合サマリー")
    
    current_age = st.session_state.user_profile['personal']['age']
    retirement_age = st.session_state.retirement_plan['target_age']
    years_to_retirement = max(retirement_age - current_age, 1)
    
    # Calculate total costs by category
    education_total = sum(plan.get('remaining_cost', 0) for plan in st.session_state.education_plans)
    
    housing = st.session_state.housing_plan
    housing_total = 0
    if housing['housing_type'] == 'rental':
        housing_total = housing['monthly_rent'] * 12 * years_to_retirement
        if housing.get('planned_purchase'):
            housing_total += housing.get('purchase_amount', 0)
    else:
        housing_total = housing.get('loan_balance', 0)
    
    vehicle_annual = 0
    for v in st.session_state.vehicle_plans:
        try:
            summary = get_vehicle_summary(
                v['vehicle_type'], v['purchase_price'], v['replacement_cycle'], v['annual_distance']
            )
            vehicle_annual += summary['annual_average_cost']
        except Exception:
            pass
    vehicle_total = vehicle_annual * years_to_retirement
    
    travel_summary = get_travel_summary(st.session_state.travel_plans)
    travel_total = travel_summary['annual_total'] * years_to_retirement
    
    other_events_total = sum(
        e['target_amount'] for e in st.session_state.life_events if e.get('category') == 'other'
    )
    
    grand_total = education_total + housing_total + vehicle_total + travel_total + other_events_total
    
    # Display summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("教育費総額", format_jpy_jpunit(education_total))
        st.metric("住宅関連総額", format_jpy_jpunit(housing_total))
    
    with col2:
        st.metric("車両関連総額", format_jpy_jpunit(vehicle_total))
        st.metric("旅行費総額", format_jpy_jpunit(travel_total))
    
    with col3:
        st.metric("その他イベント", format_jpy_jpunit(other_events_total))
        st.metric("ライフイベント総額", format_jpy_jpunit(grand_total), help=f"リタイアまでの{years_to_retirement}年間の総額")
    
    # Summary table
    summary_data = [
        {'カテゴリ': '教育費', '総額': format_jpy_jpunit(education_total), '年平均': format_jpy_jpunit(education_total / years_to_retirement)},
        {'カテゴリ': '住宅関連', '総額': format_jpy_jpunit(housing_total), '年平均': format_jpy_jpunit(housing_total / years_to_retirement)},
        {'カテゴリ': '車両関連', '総額': format_jpy_jpunit(vehicle_total), '年平均': format_jpy_jpunit(vehicle_annual)},
        {'カテゴリ': '旅行', '総額': format_jpy_jpunit(travel_total), '年平均': format_jpy_jpunit(travel_summary['annual_total'])},
        {'カテゴリ': 'その他', '総額': format_jpy_jpunit(other_events_total), '年平均': '-'},
        {'カテゴリ': '合計', '総額': format_jpy_jpunit(grand_total), '年平均': format_jpy_jpunit(grand_total / years_to_retirement)},
    ]
    
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)


def render_timeline_chart():
    """Render timeline visualization of all life events."""
    import plotly.graph_objects as go
    
    current_age = st.session_state.user_profile['personal']['age']
    retirement = st.session_state.retirement_plan
    current_year = datetime.now().year
    
    st.markdown("### ライフイベントタイムライン")
    
    fig = go.Figure()
    
    all_events = []
    
    # Education events
    for plan in st.session_state.education_plans:
        try:
            cashflow = generate_education_cashflow(plan['child_age'], plan['path_id'], plan['living_away'])
            for cf in cashflow:
                if cf['years_from_now'] > 0:
                    all_events.append({
                        'name': f"子供{plan['child_index']+1} {cf['stage']}",
                        'years_from_now': cf['years_from_now'],
                        'amount': cf['cost'],
                        'category': 'education'
                    })
        except Exception:
            pass
    
    # Housing purchase
    housing = st.session_state.housing_plan
    if housing.get('planned_purchase'):
        all_events.append({
            'name': '住宅購入',
            'years_from_now': housing['purchase_years_from_now'],
            'amount': housing['purchase_amount'],
            'category': 'housing'
        })
    
    # Vehicle replacements
    for i, vehicle in enumerate(st.session_state.vehicle_plans):
        try:
            cashflow = calculate_vehicle_cashflow(
                vehicle['vehicle_type'], vehicle['purchase_price'],
                vehicle['current_age'], vehicle['replacement_cycle'],
                vehicle['annual_distance'], 30
            )
            for cf in cashflow:
                if cf.get('is_replacement_year'):
                    all_events.append({
                        'name': f'車両{i+1}買替',
                        'years_from_now': cf['year'],
                        'amount': cf['purchase_cost'],
                        'category': 'vehicle'
                    })
        except Exception:
            pass
    
    # Other events
    for event in st.session_state.life_events:
        if event.get('category') == 'other':
            event_name = event['custom_name'] if event['type'] == 'その他' and event['custom_name'] else event['type']
            all_events.append({
                'name': event_name,
                'years_from_now': event['years_from_now'],
                'amount': event['target_amount'],
                'category': 'other'
            })
    
    if not all_events:
        st.info("ライフイベントが登録されていません")
        return
    
    # Calculate max value for axis formatting
    max_val = max(e['amount'] for e in all_events)
    min_val = 0
    tickvals, ticktext = get_axis_tickvals_ticktext(min_val, max_val, num_ticks=5)
    
    # Color mapping
    colors = {
        'education': 'blue',
        'housing': 'green',
        'vehicle': 'orange',
        'other': 'purple'
    }
    
    for event in all_events:
        event_year = current_year + event['years_from_now']
        event_age = current_age + event['years_from_now']
        
        fig.add_trace(go.Scatter(
            x=[event_year],
            y=[event['amount']],
            mode='markers',
            name=event['name'],
            marker=dict(size=12, color=colors.get(event['category'], 'gray')),
            hovertemplate=f"<b>{event['name']}</b><br>" +
                         f"時期: {event_year}年 ({event_age}歳)<br>" +
                         f"金額: {format_jpy_jpunit(event['amount'])}<extra></extra>"
        ))
    
    # Retirement line
    retirement_year = current_year + (retirement['target_age'] - current_age)
    fig.add_vline(
        x=retirement_year,
        line_dash="dash",
        line_color="red",
        annotation_text=f"リタイア ({retirement['target_age']}歳)",
        annotation_position="top"
    )
    
    fig.update_layout(
        title="ライフイベントタイムライン",
        xaxis_title="年",
        yaxis_title="金額",
        showlegend=True,
        height=500
    )
    
    fig.update_yaxes(
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext
    )
    
    st.plotly_chart(fig, use_container_width=True)


def main():
    """Main page entry point."""
    initialize_life_event_session_state()
    
    st.title("ライフイベント・リタイアメント計画")
    st.markdown("将来のライフイベントを詳細に計画し、必要資金を自動計算します")
    
    st.page_link("app.py", label="ポートフォリオ入力に戻る", icon="🏠")
    
    st.markdown("---")
    
    # Use tabs for different categories
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "教育費", "住宅", "車両", "旅行", "その他イベント", "リタイアメント"
    ])
    
    with tab1:
        education_plans = render_education_cards()
    
    with tab2:
        housing_plan = render_housing_card()
    
    with tab3:
        vehicle_plans = render_vehicle_cards()
    
    with tab4:
        travel_plans = render_travel_cards()
    
    with tab5:
        other_events = render_other_events_form()
    
    with tab6:
        retirement_data = render_retirement_plan_form()
    
    st.markdown("---")
    
    # Save button
    if st.button("計画を保存", type="primary"):
        st.session_state.education_plans = education_plans
        st.session_state.housing_plan = housing_plan
        st.session_state.vehicle_plans = vehicle_plans
        st.session_state.travel_plans = travel_plans
        st.session_state.life_events = other_events
        st.session_state.retirement_plan = retirement_data
        st.success("ライフイベント計画を保存しました")
    
    st.markdown("---")
    
    # Summary and timeline
    render_comprehensive_summary()
    render_timeline_chart()
    
    st.markdown("---")
    
    # Navigation
    st.markdown("### 次のステップ")
    col1, col2 = st.columns(2)
    with col1:
        st.page_link(
            "pages/03_ユーザープロファイル.py",
            label="プロファイル編集に戻る",
            icon="👤"
        )
    with col2:
        st.page_link(
            "pages/05_資産シミュレーション.py",
            label="資産シミュレーションへ",
            icon="📊"
        )


if __name__ == "__main__":
    main()
