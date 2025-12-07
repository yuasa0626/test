"""
Life Event and Retirement Planning Page
Allows users to register life events and set retirement goals.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.formatters import format_jpy_plain, format_jpy_jpunit, format_jpy_axis, get_axis_tickvals_ticktext

# Page configuration
st.set_page_config(
    page_title="ライフイベント・リタイアメント計画",
    page_icon="📅",
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


def initialize_life_event_session_state():
    """Initialize session state for life events."""
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {
            'personal': {'age': 30, 'occupation': '会社員'},
            'family': {'has_spouse': False, 'spouse_age': None, 'children': []},
            'cashflow': {'annual_income': 0, 'annual_expense': 0, 'monthly_investment': 0},
            'assets': {'savings': 0, 'emergency_fund': 0},
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


def render_life_events_form():
    """Render life events registration form."""
    st.markdown("### ライフイベント登録")
    st.markdown("将来予定しているライフイベントを登録してください（最大10件）")
    
    event_types = [
        '住宅購入',
        '教育費（入学金・学費）',
        '車購入',
        '結婚',
        '出産',
        '旅行',
        'その他'
    ]
    
    num_events = st.number_input(
        "登録するイベント数",
        min_value=0,
        max_value=10,
        value=len(st.session_state.life_events),
        step=1,
        key="num_events"
    )
    
    events = []
    
    if num_events > 0:
        for i in range(num_events):
            st.markdown(f"**イベント {i+1}**")
            
            default_event = st.session_state.life_events[i] if i < len(st.session_state.life_events) else {
                'type': '住宅購入',
                'custom_name': '',
                'years_from_now': 5,
                'target_amount': 5000000
            }
            
            col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
            
            with col1:
                event_type = st.selectbox(
                    "イベント種類",
                    options=event_types,
                    index=event_types.index(default_event['type']) if default_event['type'] in event_types else 0,
                    key=f"event_type_{i}"
                )
            
            with col2:
                custom_name = ""
                if event_type == 'その他':
                    custom_name = st.text_input(
                        "イベント名",
                        value=default_event.get('custom_name', ''),
                        key=f"event_custom_{i}",
                        placeholder="イベント名を入力"
                    )
                else:
                    st.text_input(
                        "イベント名",
                        value=event_type,
                        disabled=True,
                        key=f"event_name_display_{i}"
                    )
            
            with col3:
                years_from_now = st.number_input(
                    "実現時期（年後）",
                    min_value=1,
                    max_value=50,
                    value=default_event['years_from_now'],
                    step=1,
                    key=f"event_years_{i}"
                )
            
            with col4:
                target_amount = st.number_input(
                    "目標金額（円）",
                    min_value=0,
                    value=default_event['target_amount'],
                    step=100000,
                    format="%d",
                    key=f"event_amount_{i}"
                )
            
            events.append({
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


def render_events_summary():
    """Render life events summary."""
    st.markdown("### 登録済みイベント一覧")
    
    events = st.session_state.life_events
    retirement = st.session_state.retirement_plan
    current_age = st.session_state.user_profile['personal']['age']
    
    if events:
        total_amount = sum(event['target_amount'] for event in events)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            event_data = []
            for event in events:
                event_name = event['custom_name'] if event['type'] == 'その他' and event['custom_name'] else event['type']
                target_year = datetime.now().year + event['years_from_now']
                target_age = current_age + event['years_from_now']
                event_data.append({
                    'イベント': event_name,
                    '実現時期': f"{event['years_from_now']}年後 ({target_year}年)",
                    '年齢': f"{target_age}歳",
                    '目標金額': format_jpy_jpunit(event['target_amount'])
                })
            
            import pandas as pd
            st.dataframe(pd.DataFrame(event_data), use_container_width=True, hide_index=True)
        
        with col2:
            st.metric("イベント総額", format_jpy_jpunit(total_amount))
            st.metric("登録イベント数", f"{len(events)}件")
    else:
        st.info("ライフイベントが登録されていません")
    
    st.markdown("---")
    
    st.markdown("### リタイアメント計画概要")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("希望リタイア年齢", f"{retirement['target_age']}歳")
    
    with col2:
        years_to_retirement = retirement['target_age'] - current_age
        st.metric("リタイアまでの年数", f"{years_to_retirement}年")
    
    with col3:
        st.metric("リタイア後年間生活費", format_jpy_jpunit(retirement['annual_expense']))


def render_timeline_chart():
    """Render timeline visualization of life events."""
    import plotly.graph_objects as go
    
    events = st.session_state.life_events
    retirement = st.session_state.retirement_plan
    current_age = st.session_state.user_profile['personal']['age']
    
    if not events and not retirement:
        return
    
    st.markdown("### ライフイベントタイムライン")
    
    fig = go.Figure()
    
    current_year = datetime.now().year
    
    # Calculate max value for axis formatting
    if events:
        max_val = max(event['target_amount'] for event in events)
        min_val = 0
        tickvals, ticktext = get_axis_tickvals_ticktext(min_val, max_val, num_ticks=5)
    
    for i, event in enumerate(events):
        event_name = event['custom_name'] if event['type'] == 'その他' and event['custom_name'] else event['type']
        event_year = current_year + event['years_from_now']
        event_age = current_age + event['years_from_now']
        
        fig.add_trace(go.Scatter(
            x=[event_year],
            y=[event['target_amount']],
            mode='markers+text',
            name=event_name,
            text=[f"{event_name}<br>{format_jpy_jpunit(event['target_amount'])}"],
            textposition='top center',
            marker=dict(size=15, symbol='circle'),
            hovertemplate=f"<b>{event_name}</b><br>" +
                         f"時期: {event_year}年 ({event_age}歳)<br>" +
                         f"金額: {format_jpy_jpunit(event['target_amount'])}<extra></extra>"
        ))
    
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
        height=400
    )
    
    # Use Japanese format for Y-axis if events exist
    if events:
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
    st.markdown("将来のライフイベントとリタイアメント計画を設定してください")
    
    st.page_link("app.py", label="ポートフォリオ入力に戻る", icon="🏠")
    
    st.markdown("---")
    
    with st.form(key="life_events_form"):
        events_data = render_life_events_form()
        
        st.markdown("---")
        
        retirement_data = render_retirement_plan_form()
        
        st.markdown("---")
        
        submitted = st.form_submit_button("計画を保存", type="primary")
        
        if submitted:
            st.session_state.life_events = events_data
            st.session_state.retirement_plan = retirement_data
            st.success("ライフイベント・リタイアメント計画を保存しました")
    
    st.markdown("---")
    
    render_events_summary()
    
    render_timeline_chart()
    
    st.markdown("---")
    
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
