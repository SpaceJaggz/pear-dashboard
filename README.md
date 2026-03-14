# 🍐 Pear Protocol Dashboard

Track notional volume and referrals for Pear Protocol traders on Hyperliquid.

## Pages
- **🏅 Ambassador** — Volume + referral tracking for ambassadors
- **⭐ VIPs** — Volume tracking for VIP traders

## Quick Start

### 1. Setup Google Sheets
Create a Google Sheet with 2 tabs:

**Ambassadors tab:**
| address | name | refcode | status |
|---------|------|---------|--------|
| 0xAbC...| Alice| ALICE_REF| active|

**VIPs tab:**
| address | name | status |
|---------|------|--------|
| 0x123...| Whale| active |

Publish each tab: `File → Share → Publish to web → CSV`

### 2. Configure
Set the CSV URLs in `fetch_data.py` (lines 24-29) or as environment variables:
```
AMBASSADORS_CSV_URL=https://docs.google.com/spreadsheets/d/e/XXX/pub?gid=0&output=csv
VIPS_CSV_URL=https://docs.google.com/spreadsheets/d/e/XXX/pub?gid=123&output=csv
```

### 3. Fetch Data
```bash
pip install -r requirements.txt
python fetch_data.py
```

### 4. Run Dashboard Locally
```bash
streamlit run app.py
```

### 5. Deploy to Streamlit Cloud
1. Push this repo to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect your GitHub repo
4. Set main file: `app.py`
5. Add secrets (Settings → Secrets):
   ```toml
   AMBASSADORS_CSV_URL = "your_url_here"
   VIPS_CSV_URL = "your_url_here"
   ```

### 6. Auto-update (GitHub Actions)
Add repository secrets:
- `AMBASSADORS_CSV_URL`
- `VIPS_CSV_URL`

The workflow runs daily at 07:00 WIB. Trigger manually via Actions tab.

## Adding Pear Referral API Later
See `fetch_data.py` lines 44-75 for the placeholder. When you get the API:
1. Uncomment the `fetch_pear_referrals()` function
2. Add the API URL and key
3. Call it in `process_ambassadors()`
4. Dashboard auto-displays new fields

## Data Sources
- **Hyperliquid API** (`api.hyperliquid.xyz`) — trade fills, referral data
- **Pear Builder Address** — `0xA47D4d99191db54A4829cdf3de2417E527c3b042`
- **Google Sheets** — address input management
