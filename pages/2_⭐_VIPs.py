"""
⭐ VIPs Page
Displays notional volume data for VIP traders on Pear Protocol.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import load_data, format_volume, short_address, parse_timestamp

st.set_page_config(page_title="⭐ VIPs — Pear Dashboard", page_icon="🍐", layout="wide")

# Custom CSS
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

# Sidebar
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
total_vol_24h = sum(v["pear"]["volume_24h"] for v in vips)
total_vol_7d = sum(v["pear"]["volume_7d"] for v in vips)
total_trades = sum(v["pear"]["total_trades"] for v in vips)

c1, c2, c3, c4 = st.columns(4)
c1.metric("VIP Traders", len(vips))
c2.metric("Total Pear Volume", format_volume(total_vol))
c3.metric("Volume 24h", format_volume(total_vol_24h))
c4.metric("Total Trades", f"{total_trades:,}")

st.markdown("---")


# ─── Main Table ───
st.markdown("### 📊 VIP Volume Table")

table_data = []
for v in vips:
    table_data.append({
        "Name": v["name"],
        "Address": short_address(v["address"]),
        "Full Address": v["address"],
        "Vol 24h ($)": v["pear"]["volume_24h"],
        "Vol 7d ($)": v["pear"]["volume_7d"],
        "Vol 30d ($)": v["pear"]["volume_30d"],
        "Total Vol ($)": v["pear"]["total_volume"],
        "Trades": v["pear"]["total_trades"],
        "Fees ($)": v["pear"]["total_fees"],
        "Open Vol ($)": v["pear"]["open_volume"],
        "Close Vol ($)": v["pear"]["close_volume"],
    })

df = pd.DataFrame(table_data)

st.dataframe(
    df.drop(columns=["Full Address"]).style.format({
        "Vol 24h ($)": "${:,.0f}",
        "Vol 7d ($)": "${:,.0f}",
        "Vol 30d ($)": "${:,.0f}",
        "Total Vol ($)": "${:,.0f}",
        "Trades": "{:,}",
        "Fees ($)": "${:,.2f}",
        "Open Vol ($)": "${:,.0f}",
        "Close Vol ($)": "${:,.0f}",
    }),
    use_container_width=True,
    height=min(400, 60 + len(vips) * 40),
)

st.markdown("---")


# ─── Volume Comparison ───
st.markdown("### 📈 Volume Comparison")

col1, col2 = st.columns(2)

with col1:
    fig_bar = px.bar(
        df.sort_values("Total Vol ($)", ascending=True),
        x="Total Vol ($)", y="Name",
        orientation="h",
        color="Total Vol ($)",
        color_continuous_scale=["#FFE8CC", "#E8590C", "#D9480F"],
        labels={"Total Vol ($)": "Total Pear Volume (USDC)", "Name": ""},
    )
    fig_bar.update_layout(
        title="Total Volume",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        coloraxis_showscale=False,
        height=max(300, len(vips) * 60),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(tickformat="$,.0f"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    # Open vs Close volume pie
    fig_pie = go.Figure(data=[go.Pie(
        labels=["Open Volume", "Close Volume"],
        values=[
            sum(v["pear"]["open_volume"] for v in vips),
            sum(v["pear"]["close_volume"] for v in vips),
        ],
        marker_colors=["#2D6A4F", "#E8590C"],
        hole=0.5,
        textinfo="label+percent",
    )])
    fig_pie.update_layout(
        title="Open vs Close Volume (All VIPs)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=max(300, len(vips) * 60),
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")


# ─── Detail View per VIP ───
st.markdown("### 🔍 VIP Detail")

selected_name = st.selectbox(
    "Select VIP",
    [v["name"] for v in vips],
)

selected = next(v for v in vips if v["name"] == selected_name)

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

    fig_daily = go.Figure()
    fig_daily.add_trace(go.Bar(
        x=daily_df["Date"], y=daily_df["Volume"],
        marker_color="#E8590C",
        marker_line_width=0,
        name="Daily Volume",
    ))
    fig_daily.add_trace(go.Scatter(
        x=daily_df["Date"], y=daily_df["Volume"].rolling(7, min_periods=1).mean(),
        mode="lines",
        line=dict(color="#1B4332", width=2.5),
        name="7d Moving Avg",
    ))
    fig_daily.update_layout(
        title=f"Daily Pear Volume — {selected_name}",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=350,
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis=dict(tickformat="$,.0f", title=""),
        xaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_daily, use_container_width=True)

# Additional info
with st.expander("ℹ️ Full Address & Hyperliquid Stats"):
    st.code(selected["address"])
    hl = selected.get("all_hyperliquid", {})
    st.markdown(f"""
    - **Total Hyperliquid Volume:** {format_volume(hl.get('total_volume', 0))}
    - **Total Hyperliquid Trades:** {hl.get('total_trades', 0):,}
    - **Pear % of Total:** {(selected['pear']['total_volume'] / max(hl.get('total_volume', 1), 1)) * 100:.1f}%
    """)
