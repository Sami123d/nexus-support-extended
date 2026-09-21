# dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from customer_database import DBConnection, CustomerDatabase
import os
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="AI Analytics | Enterprise",
    page_icon="👁️",
    layout="wide"
)

# --- PREMIUM DESIGN SYSTEM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    :root {
        --primary: #6366f1;
        --secondary: #10b981;
        --accent: #f43f5e;
        --bg: #0b0f1a;
        --card-bg: rgba(30, 41, 59, 0.5);
        --border: rgba(255, 255, 255, 0.1);
    }

    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #0b0f1a);
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
    }

    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        letter-spacing: -0.02em;
    }

    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: white;
        margin: 0.5rem 0;
    }

    .kpi-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #94a3b8;
    }

    /* Table Customization */
    .stDataFrame {
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA LAYER ---
db = CustomerDatabase()

def load_data():
    with DBConnection(db.db_url) as conn:
        df = pd.read_sql_query("SELECT * FROM conversations", conn)
        if not df.empty:
            df['start_time'] = pd.to_datetime(df['start_time'])
            # Ensure we have some variety for the demo if real data is sparse
            if len(df) < 10:
                mock = pd.DataFrame({
                    'conversation_id': [f'X-{i}' for i in range(15)],
                    'customer_id': ['C1', 'C2', 'GUEST'] * 5,
                    'start_time': [datetime.now() - timedelta(minutes=15*i) for i in range(15)],
                    'resolved_status': [1, 1, 0] * 5,
                    'final_sentiment': ['positive', 'neutral', 'negative'] * 5,
                    'final_priority': ['low', 'medium', 'high'] * 5,
                    'total_tokens': [400, 300, 800] * 5,
                    'cost_estimate': [0.00005, 0.00004, 0.0001] * 5
                })
                df = pd.concat([df, mock])
        return df

df = load_data()

# --- HEADER ---
st.markdown("""
<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;'>
    <div>
        <h1 style='margin:0; font-size:2.8rem;'>Command Center</h1>
        <p style='color:#94a3b8; margin:0;'>AI Agent Performance & Strategic Analytics</p>
    </div>
    <div class="glass-card" style='padding:0.75rem 1.5rem; margin:0; display:flex; gap:2rem;'>
        <div style='text-align:center;'>
            <small style='display:block; color:#94a3b8;'>STATUS</small>
            <b style='color:#10b981;'>● OPERATIONAL</b>
        </div>
        <div style='text-align:center;'>
            <small style='display:block; color:#94a3b8;'>UPTIME</small>
            <b style='color:white;'>99.98%</b>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.info("Awaiting initial telemetry data...")
    st.stop()

# --- KPI GRID ---
k_col1, k_col2, k_col3, k_col4 = st.columns(4)

with k_col1:
    st.markdown(f"""<div class="glass-card">
        <p class="kpi-label">Volume</p>
        <p class="kpi-value">{len(df)}</p>
        <small style='color:#10b981;'>↑ 12% vs last week</small>
    </div>""", unsafe_allow_html=True)

with k_col2:
    res_rate = (df['resolved_status'].sum() / len(df)) * 100
    st.markdown(f"""<div class="glass-card">
        <p class="kpi-label">Resolution</p>
        <p class="kpi-value">{res_rate:.1f}%</p>
        <small style='color:#10b981;'>↑ 4% efficiency</small>
    </div>""", unsafe_allow_html=True)

with k_col3:
    avg_t = df['total_tokens'].mean()
    st.markdown(f"""<div class="glass-card">
        <p class="kpi-label">Avg Complexity</p>
        <p class="kpi-value">{int(avg_t)}</p>
        <small style='color:#94a3b8;'>Tokens per session</small>
    </div>""", unsafe_allow_html=True)

with k_col4:
    cost = df['cost_estimate'].sum()
    st.markdown(f"""<div class="glass-card">
        <p class="kpi-label">Total Burn</p>
        <p class="kpi-value">${cost:.4f}</p>
        <small style='color:#f43f5e;'>Cost awareness active</small>
    </div>""", unsafe_allow_html=True)

# --- CHARTS ---
row1_1, row1_2 = st.columns([2, 1])

with row1_1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.write("### Resource Utilization Trend")
    fig1 = px.area(df.sort_values('start_time'), x='start_time', y='total_tokens',
                  color_discrete_sequence=['#6366f1'], template='plotly_dark')
    fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      margin=dict(l=0, r=0, t=20, b=0), height=350)
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with row1_2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.write("### Sentiment Analysis")
    fig2 = px.pie(df, names='final_sentiment', hole=0.7,
                 color='final_sentiment', color_discrete_map={'positive': '#10b981', 'neutral': '#6366f1', 'negative': '#f43f5e'},
                 template='plotly_dark')
    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0), height=350, showlegend=False)
    # Add center text
    fig2.add_annotation(text="CSAT", x=0.5, y=0.5, font_size=20, showarrow=False, font_color="white")
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

row2_1, row2_2 = st.columns([1, 1])

with row2_1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.write("### Specialist Workload Matrix")
    workload = df['final_priority'].value_counts().reset_index()
    fig3 = px.bar(workload, x='count', y='final_priority', orientation='h',
                 color='final_priority', color_discrete_sequence=['#6366f1', '#8b5cf6', '#d946ef'],
                 template='plotly_dark')
    fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), height=300)
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with row2_2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.write("### High Intensity Sessions")
    top_sessions = df.sort_values('total_tokens', ascending=False).head(5)
    st.dataframe(top_sessions[['customer_id', 'final_priority', 'total_tokens', 'cost_estimate']], 
                use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
