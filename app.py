"""
🍐 Pear Protocol Dashboard
Main entry point — redirects to Ambassador page by default.
"""
import streamlit as st

st.set_page_config(
    page_title="🍐 Pear Protocol Dashboard",
    page_icon="🍐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global */
    .stApp { font-family: 'DM Sans', sans-serif; }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1B4332 0%, #2D6A4F 100%);
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown h5 {
        color: #D8F3DC !important;
    }
    [data-testid="stSidebarNavItems"] span { color: #FFFFFF !important; }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #F0F7F4 0%, #D8F3DC 100%);
        border: 1px solid #B7E4C7;
        border-radius: 12px;
        padding: 16px 20px;
    }
    [data-testid="stMetric"] label {
        color: #2D6A4F !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1B4332 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Headers */
    h1 { color: #1B4332 !important; font-weight: 700 !important; }
    h2, h3 { color: #2D6A4F !important; }
    
    /* Tables */
    .stDataFrame { border-radius: 8px; overflow: hidden; }
    
    /* Hide default Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Status badge */
    .status-active {
        background: #D8F3DC; color: #1B4332;
        padding: 2px 10px; border-radius: 12px;
        font-size: 0.8em; font-weight: 600;
    }
    .status-inactive {
        background: #FFE3E3; color: #C92A2A;
        padding: 2px 10px; border-radius: 12px;
        font-size: 0.8em; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("# 🍐 Pear Protocol")
    st.markdown("##### Ambassador and VIP Volume Monitoring Dashboard")
    st.markdown("---")
    st.markdown("""
    **Pages:**
    - 🏅 Ambassador — Volume + Referrals
    - ⭐ VIPs — Volume Tracking
    
    ---
    
    **Data Source:**
    - Hyperliquid API
    - Pear Builder Fills
    - Google Sheets (address input)
    
    ---
    *Updated daily at 07:00 WIB*
    """)

# Landing page
st.markdown("# 🍐 Pear Protocol Dashboard")
st.markdown("Track notional volume and referrals for Pear Protocol traders on Hyperliquid.")
st.markdown("")
st.info("👈 **Select a page from the sidebar** to view Ambassador or VIP data.")
st.markdown("")

col1, col2 = st.columns(2)
with col1:
    st.markdown("### 🏅 Ambassador Page")
    st.markdown("""
    - Notional volume (open & close) via Pear
    - Referral volume from reflinks
    - Referee tracking per ambassador
    - Daily volume charts
    """)
with col2:
    st.markdown("### ⭐ VIPs Page")
    st.markdown("""
    - Notional volume (open & close) via Pear
    - Daily volume breakdown
    - Trade count tracking
    - Volume trend charts
    """)
