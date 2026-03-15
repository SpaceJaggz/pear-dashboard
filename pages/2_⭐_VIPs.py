"""
⭐ VIPs Page
Displays notional volume data for VIP traders on Pear Protocol.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import load_data, format_volume, short_address, parse_timestamp

st.set_page_config(page_title="⭐ VIPs — Pear Dashboard", page_icon="🍐", layout="wide")

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
        background: linear-gradient(135deg, #FFF4E6 0%, #FFE8CC 100%);
        border: 1px solid #FFD8A8; border-radius: 12px; padding: 16px 20px;
    }
    [data-testid="stMetric"] label { color: #E8590C !important; font-weight: 500 !important; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #D9480F !important; font-family: 'JetBrains Mono', monospace !important;
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
raw = load_data("vips.json")
vips = raw.get("data", [])
generated_at = raw.get("generated_at", "N/A")

st.markdown("# ⭐ VIP Dashboard")
st.caption(f"Last updated: {parse_timestamp(generated_at)}")

if not vips:
    st.warning("No VIP data found. Run `fetch_data.py` first or check your data files.")
    st.stop()

# ─── Summary Cards ───
total_vol = sum(v["pear"]["total_volume"] for v in vips)
total_fees = sum(v["pear"]["total_fees"] for v in vips)

c1, c2, c3 = st.columns(3)
c1.metric("VIP Traders", len(vips))
c2.metric("Total Pear Volume", format_volume(total_vol))
c3.metric("Total Fees Paid", format_volume(total_fees))

st.markdown("---")

# ─── Main Table ───
st.markdown("### 📊 VIP Volume Table")

table_data = []
for v in vips:
    table_data.append({
        "Name": v["name"],
        "Address": short_address(v["address"]),
        "Total Volume ($)": v["pear"]["total_volume"],
        "Fees Paid ($)": v["pear"]["total_fees"],
        "Builder Fees ($)": v["pear"]["total_builder_fees"],
    })

df = pd.DataFrame(table_data)
df.index = df.index + 1  # Start numbering from 1

st.dataframe(
    df.style.format({
        "Total Volume ($)": "${:,.0f}",
        "Fees Paid ($)": "${:,.2f}",
        "Builder Fees ($)": "${:,.2f}",
    }),
    use_container_width=True,
    height=min(500, 60 + len(vips) * 40),
)

st.markdown("---")

# ─── Volume Comparison ───
st.markdown("### 📈 Volume Comparison")

fig_bar = px.bar(
    df.sort_values("Total Volume ($)", ascending=True),
    x="Total Volume ($)", y="Name",
    orientation="h",
    color="Total Volume ($)",
    color_continuous_scale=["#FFE8CC", "#E8590C", "#D9480F"],
    labels={"Total Volume ($)": "Total Pear Volume (USDC)", "Name": ""},
)
fig_bar.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    coloraxis_showscale=False,
    height=max(300, len(vips) * 50),
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(tickformat="$,.0f"),
)
st.plotly_chart(fig_bar, use_container_width=True)
