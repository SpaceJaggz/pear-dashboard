"""
🏅 Ambassador Page
Displays notional volume and referral data for Pear Protocol ambassadors.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import load_data, format_volume, short_address, parse_timestamp

st.set_page_config(page_title="🏅 Ambassadors — Pear Dashboard", page_icon="🍐", layout="wide")

# Load custom CSS (same as main app)
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

# Sidebar
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
total_referees = sum(a.get("referral", {}).get("referee_count", 0) for a in ambassadors)
total_vol_24h = sum(a["pear"]["volume_24h"] for a in ambassadors)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ambassadors", len(ambassadors))
c2.metric("Total Pear Volume", format_volume(total_pear_vol))
c3.metric("Total Referral Volume", format_volume(total_ref_vol))
c4.metric("Volume 24h", format_volume(total_vol_24h))

st.markdown("---")


# ─── Main Table ───
st.markdown("### 📊 Ambassador Volume Table")

# Build dataframe for display
table_data = []
for a in ambassadors:
    ref = a.get("referral", {})
    table_data.append({
        "Name": a["name"],
        "Address": short_address(a["address"]),
        "Full Address": a["address"],
        "Ref Code": a.get("refcode", "—"),
        "Vol 24h ($)": a["pear"]["volume_24h"],
        "Vol 7d ($)": a["pear"]["volume_7d"],
        "Vol 30d ($)": a["pear"]["volume_30d"],
        "Total Vol ($)": a["pear"]["total_volume"],
        "Trades": a["pear"]["total_trades"],
        "Ref Volume ($)": ref.get("total_referral_volume", 0),
        "Referees": ref.get("referee_count", 0),
        "Rewards ($)": ref.get("rewards_claimed", 0) + ref.get("rewards_unclaimed", 0),
    })

df = pd.DataFrame(table_data)

# Display sortable table
st.dataframe(
    df.drop(columns=["Full Address"]).style.format({
        "Vol 24h ($)": "${:,.0f}",
        "Vol 7d ($)": "${:,.0f}",
        "Vol 30d ($)": "${:,.0f}",
        "Total Vol ($)": "${:,.0f}",
        "Trades": "{:,}",
        "Ref Volume ($)": "${:,.0f}",
        "Referees": "{:,}",
        "Rewards ($)": "${:,.2f}",
    }),
    use_container_width=True,
    height=min(400, 60 + len(ambassadors) * 40),
)

st.markdown("---")


# ─── Volume Comparison Chart ───
st.markdown("### 📈 Volume Comparison")

tab1, tab2 = st.tabs(["Pear Volume", "Referral Volume"])

with tab1:
    fig = px.bar(
        df.sort_values("Total Vol ($)", ascending=True),
        x="Total Vol ($)", y="Name",
        orientation="h",
        color="Total Vol ($)",
        color_continuous_scale=["#B7E4C7", "#2D6A4F", "#1B4332"],
        labels={"Total Vol ($)": "Notional Volume (USDC)", "Name": ""},
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        coloraxis_showscale=False,
        height=max(300, len(ambassadors) * 60),
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
        height=max(300, len(ambassadors) * 60),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(tickformat="$,.0f"),
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")


# ─── Detail View per Ambassador ───
st.markdown("### 🔍 Ambassador Detail")

selected_name = st.selectbox(
    "Select Ambassador",
    [a["name"] for a in ambassadors],
)

selected = next(a for a in ambassadors if a["name"] == selected_name)

# Detail metrics
dc1, dc2, dc3, dc4 = st.columns(4)
dc1.metric("Open Volume", format_volume(selected["pear"]["open_volume"]))
dc2.metric("Close Volume", format_volume(selected["pear"]["close_volume"]))
dc3.metric("Total Fees", f"${selected['pear']['total_fees']:,.2f}")
dc4.metric("Builder Fees", f"${selected['pear']['total_builder_fees']:,.2f}")

# Daily volume chart
daily = selected["pear"].get("daily_volumes", {})
if daily:
    daily_df = pd.DataFrame([
        {"Date": k, "Volume": v} for k, v in daily.items()
    ])
    daily_df["Date"] = pd.to_datetime(daily_df["Date"])
    daily_df = daily_df.sort_values("Date")

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=daily_df["Date"], y=daily_df["Volume"],
        marker_color="#2D6A4F",
        marker_line_width=0,
        name="Daily Volume",
    ))
    fig3.add_trace(go.Scatter(
        x=daily_df["Date"], y=daily_df["Volume"].rolling(7, min_periods=1).mean(),
        mode="lines",
        line=dict(color="#B7094C", width=2.5),
        name="7d Moving Avg",
    ))
    fig3.update_layout(
        title=f"Daily Pear Volume — {selected_name}",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=350,
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis=dict(tickformat="$,.0f", title=""),
        xaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig3, use_container_width=True)

# Referral details
ref_data = selected.get("referral", {})
if ref_data and ref_data.get("referees"):
    st.markdown(f"#### 🤝 Referees ({ref_data['referee_count']})")

    ref_note = ref_data.get("source", "hyperliquid")
    if ref_note == "hyperliquid":
        st.caption("⚠️ Referral data from Hyperliquid (all trading, not only via Pear). Will be updated to Pear-specific when API is available.")

    referee_df = pd.DataFrame([
        {
            "Address": short_address(r["address"]),
            "Volume ($)": r["volume"],
            "Fees Rewarded ($)": r["fees_rewarded"],
            "Joined": parse_timestamp(r["joined"]),
        }
        for r in ref_data["referees"]
    ]).sort_values("Volume ($)", ascending=False)

    st.dataframe(
        referee_df.style.format({
            "Volume ($)": "${:,.0f}",
            "Fees Rewarded ($)": "${:,.2f}",
        }),
        use_container_width=True,
        height=min(400, 60 + len(ref_data["referees"]) * 40),
    )

    # Rewards summary
    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Rewards Claimed", f"${ref_data.get('rewards_claimed', 0):,.2f}")
    rc2.metric("Rewards Unclaimed", f"${ref_data.get('rewards_unclaimed', 0):,.2f}")
    rc3.metric("Builder Rewards", f"${ref_data.get('builder_rewards', 0):,.2f}")
