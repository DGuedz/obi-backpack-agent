import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time

# --- Configuração da Página ---
st.set_page_config(
    page_title="OBI WORK | Tactical Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Personalizado (Iron Dome Theme) ---
st.markdown("""
<style>
    .stApp {
        background-color: #000000;
        color: #e4e4e7;
    }
    .stMetric {
        background-color: #18181b;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #27272a;
    }
    div[data-testid="stMetricValue"] {
        color: #10b981; /* Emerald-500 */
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }
    h1, h2, h3 {
        font-family: 'Courier New', monospace;
        color: #ffffff;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .status-live {
        background-color: #064e3b;
        color: #34d399;
        border: 1px solid #059669;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title(" OBI WORK")
    st.caption("Protocol Omega v4.0")
    
    st.markdown("---")
    
    st.subheader("System Status")
    st.markdown('<span class="status-badge status-live">● SYSTEM ONLINE</span>', unsafe_allow_html=True)
    st.markdown(f"**Latency:** {np.random.randint(15, 45)}ms")
    st.markdown("**Iron Dome:** ACTIVE")
    
    st.markdown("---")
    
    tier = st.selectbox("License Tier", ["SCOUT", "COMMANDER", "ARCHITECT"])
    mode = st.radio("Operation Mode", ["Sniper (HFT)", "Weaver (Grid)", "Harvester (Yield)"])

# --- Main Content ---
col1, col2 = st.columns([3, 1])

with col1:
    st.title("TACTICAL DASHBOARD")
    st.markdown(f"Current Operation: **{mode}** | Tier: **{tier}**")

with col2:
    st.markdown("###  Live Feed")
    st.text(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")

# --- Metrics Row ---
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Daily PnL", "+$124.50", "2.4%")
with m2:
    st.metric("Open Interest (OBI)", "High", "+15%")
with m3:
    st.metric("Active Grids", "12", "SOL_USDC")
with m4:
    st.metric("Risk Exposure", "18%", "-2%")

# --- Charts Area ---
tab1, tab2 = st.tabs(["Performance", "Market Depth (OBI)"])

with tab1:
    # Mock Data for Chart
    dates = pd.date_range(start="2024-01-01", periods=100)
    prices = np.cumsum(np.random.randn(100)) + 100
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines', name='Equity Curve', line=dict(color='#10b981')))
    fig.update_layout(
        title="Equity Curve (Simulated)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e4e4e7'),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#27272a')
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.info(" Access restricted to ARCHITECT Tier. Upgrade to view live Order Book Imbalance.")

# --- Logs Console ---
st.markdown("###  Terminal Output")
logs = [
    "[10:42:15] INFO: Weaver Grid initialized on SOL_USDC",
    "[10:42:18] SUCCESS: Buy Order #9928 filled @ 142.50",
    "[10:43:05] WARNING: Volatility Spike detected (ATR > 2.5). Widening spreads...",
    "[10:44:12] INFO: Iron Dome check passed. 0 threats detected."
]
st.code("\n".join(logs), language="bash")
