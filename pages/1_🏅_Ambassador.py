"""
🏅 Ambassador Page
Displays notional volume and referral data for Pear Protocol ambassadors.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import load_data, format_volume, short_address, parse_timestamp

st.set_page_config(page_title="🏅 Ambassadors — Pear Dashboard", page_icon="🍐", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');
    .stApp { font-family: 'DM Sans', sans-serif; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1B4332 0%, #2D6A4F 100%); }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown h5 { color: #D8F3DC !important; }
    [data-testid="stSidebarNavItems"] span { color: #FFFFFF !important; }
    [data-testid="stSidebarNavItems"] li:first-child { display: none; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #F0F7F4 0%, #D8F3DC 100%);
        border: 1px solid #B7E4C7; border-radius: 12px; padding: 16px 20px;
    }
    [data-testid="stMetric"] label { color: #2D6A4F !important; font-weight: 500 !important; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1B4332 !important; font-family: 'JetBrains Mono', monospace !important;
    }
    h1 { color: #1B4332 !important; font-weight: 700 !important; }
    h2, h3 { color: #2D6A4F !important; }
    #MainMenu { visibility: hidden; } footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("# 🍐 Pear Protocol")
    st.markdown("##### Ambassador and VIP Volume Monitoring Dashboard")
    st.markdown("---")

# ─── Load Data ───
raw = load_data("ambassadors.json")
ambassadors = raw.get("data", [])
generated_at = raw.get("generated_at", "N/A")

st.markdown("# 🏅 Ambassador Dashboard")
st.caption(f"Last updated: {parse_timestamp(generated_at)}")

if not ambassadors:
    st.warning("No ambassador data found. Run `fetch_data.py` first or check your data files.")
    st.stop()

# ─── Summary Cards ───
total_pear_vol = sum(a["pear"]["total_volume"] for a in ambassadors)
total_ref_vol = sum(a.get("referral", {}).get("total_referral_volume", 0) for a in ambassadors)
total_referees = sum(a.get("referral", {}).get("total_referees", 0) for a in ambassadors)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ambassadors", len(ambassadors))
c2.metric("Total Pear Volume", format_volume(total_pear_vol))
c3.metric("Total Referral Volume", format_volume(total_ref_vol))
c4.metric("Total Referees", f"{total_referees:,}")

st.markdown("---")

# ─── Main Table ───
st.markdown("### 📊 Ambassador Volume Table")

table_data = []
for a in ambassadors:
    ref = a.get("referral", {})
    table_data.append({
        "Name": a["name"],
        "Address": short_address(a["address"]),
        "Ref Code": a.get("refcode", "—") or "—",
        "Total Volume ($)": a["pear"]["total_volume"],
        "Fees Paid ($)": a["pear"]["total_fees"],
        "Builder Fees ($)": a["pear"]["total_builder_fees"],
        "Ref Volume ($)": ref.get("total_referral_volume", 0),
        "Referees": ref.get("total_referees", 0),
    })

df = pd.DataFrame(table_data)
df.index = df.index + 1  # Start numbering from 1

st.dataframe(
    df.style.format({
        "Total Volume ($)": "${:,.0f}",
        "Fees Paid ($)": "${:,.2f}",
        "Builder Fees ($)": "${:,.2f}",
        "Ref Volume ($)": "${:,.0f}",
        "Referees": "{:,}",
    }),
    use_container_width=True,
    height=min(500, 60 + len(ambassadors) * 40),
)

st.markdown("---")

# ─── Volume Comparison Charts ───
st.markdown("### 📈 Volume Comparison")

tab1, tab2 = st.tabs(["Pear Volume", "Referral Volume"])

with tab1:
    fig = px.bar(
        df.sort_values("Total Volume ($)", ascending=True),
        x="Total Volume ($)", y="Name",
        orientation="h",
        color="Total Volume ($)",
        color_continuous_scale=["#B7E4C7", "#2D6A4F", "#1B4332"],
        labels={"Total Volume ($)": "Notional Volume (USDC)", "Name": ""},
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        coloraxis_showscale=False,
        height=max(300, len(ambassadors) * 50),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(tickformat="$,.0f"),
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig2 = px.bar(
        df.sort_values("Ref Volume ($)", ascending=True),
        x="Ref Volume ($)", y="Name",
        orientation="h",
        color="Ref Volume ($)",
        color_continuous_scale=["#FFE3E3", "#FF8787", "#C92A2A"],
        labels={"Ref Volume ($)": "Referral Volume (USDC)", "Name": ""},
    )
    fig2.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        coloraxis_showscale=False,
        height=max(300, len(ambassadors) * 50),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(tickformat="$,.0f"),
    )
    st.plotly_chart(fig2, use_container_width=True)
