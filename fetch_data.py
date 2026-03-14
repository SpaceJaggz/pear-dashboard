"""
Pear Protocol Dashboard — Data Fetcher
=======================================
Fetches trading volume data from Hyperliquid API for tracked addresses.
Identifies Pear Protocol trades via builder fees.
Outputs JSON files for the Streamlit dashboard.

Usage:
    python fetch_data.py

Environment variables (optional):
    AMBASSADORS_CSV_URL  — Published Google Sheets CSV URL for Ambassadors
    VIPS_CSV_URL         — Published Google Sheets CSV URL for VIPs
"""

import os
import io
import json
import time
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path

# =============================================================================
# CONFIGURATION — Edit these values
# =============================================================================

# Google Sheets "Publish to web" CSV URLs
# Replace with your actual published CSV URLs
AMBASSADORS_CSV_URL = os.environ.get(
    "AMBASSADORS_CSV_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQwS66TXQGEBmbnaBBLikcOnWbAe6_sg2zgBx1FpqVdRptOfhDjB076bCAz4In3CPKEF05pUtcwrTG8/pub?gid=0&single=true&output=csv"
)
VIPS_CSV_URL = os.environ.get(
    "VIPS_CSV_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQwS66TXQGEBmbnaBBLikcOnWbAe6_sg2zgBx1FpqVdRptOfhDjB076bCAz4In3CPKEF05pUtcwrTG8/pub?gid=2090993430&single=true&output=csv"
)

# Pear Protocol builder address on Hyperliquid (lowercase!)
PEAR_BUILDER_ADDRESS = "0xa47d4d99191db54a4829cdf3de2417e527c3b042"

# Hyperliquid API
HL_API_URL = "https://api.hyperliquid.xyz/info"

# Pear Protocol builder fills base URL
BUILDER_FILLS_BASE = "https://stats-data.hyperliquid.xyz/Mainnet/builder_fills"

# Output directory
DATA_DIR = Path(__file__).parent / "data"

# Rate limit delay between API calls (seconds)
API_DELAY = 1.0  # seconds between API calls (avoid 429 rate limit)

# =============================================================================
# PLACEHOLDER: Pear Protocol Referral API
# =============================================================================
# Uncomment and configure when you receive the API details from Pear team.
#
# PEAR_REFERRAL_API_URL = "https://hl-v2.pearprotocol.io/api/referral"
# PEAR_API_KEY = os.environ.get("PEAR_API_KEY", "")
#
# def fetch_pear_referrals(address: str) -> dict:
#     """
#     Fetch Pear-specific referral data for an address.
#     Replace the implementation below with actual Pear API call.
#
#     Expected response format (adjust to actual API):
#     {
#         "referralCode": "ALICE_REF",
#         "referees": [
#             {"address": "0x...", "volume": "52000.50", "joinedAt": "..."},
#         ],
#         "totalReferralVolume": "150000.00",
#         "rewards": {"claimed": "15.5", "unclaimed": "3.2"}
#     }
#     """
#     headers = {"Authorization": f"Bearer {PEAR_API_KEY}"} if PEAR_API_KEY else {}
#     try:
#         resp = requests.get(
#             f"{PEAR_REFERRAL_API_URL}/{address}",
#             headers=headers,
#             timeout=15
#         )
#         resp.raise_for_status()
#         return resp.json()
#     except Exception as e:
#         print(f"  [WARN] Pear referral API error for {address}: {e}")
#         return {}
#
# To integrate:
# 1. Uncomment the code above
# 2. In process_ambassadors(), add after the HL referral fetch:
#        pear_ref = fetch_pear_referrals(address)
#        if pear_ref:
#            record["pear_referral_volume"] = float(pear_ref.get("totalReferralVolume", 0))
#            record["pear_referees"] = pear_ref.get("referees", [])
#            record["pear_rewards"] = pear_ref.get("rewards", {})
# 3. The dashboard will automatically pick up the new fields
# =============================================================================


def log(msg: str):
    """Simple timestamped logging."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


# =============================================================================
# GOOGLE SHEETS READER
# =============================================================================

def read_google_sheet(csv_url: str) -> pd.DataFrame:
    """Read a published Google Sheets CSV URL into a DataFrame."""
    log(f"Reading sheet from: {csv_url[:80]}...")
    try:
        resp = requests.get(csv_url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]
        # Filter active only
        if "status" in df.columns:
            df = df[df["status"].str.strip().str.lower() == "active"]
        log(f"  Found {len(df)} active addresses")
        return df
    except Exception as e:
        log(f"  [ERROR] Failed to read sheet: {e}")
        return pd.DataFrame()


# =============================================================================
# HYPERLIQUID API CALLS
# =============================================================================

def hl_post(payload: dict, retries: int = 3) -> dict | list:
    """Make a POST request to Hyperliquid Info API with retry on rate limit."""
    for attempt in range(retries):
        try:
            resp = requests.post(HL_API_URL, json=payload, timeout=30)
            if resp.status_code == 429:
                wait = 5 * (attempt + 1)  # 5s, 10s, 15s
                log(f"  [RATE LIMIT] Waiting {wait}s before retry ({attempt + 1}/{retries})...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if "429" in str(e) and attempt < retries - 1:
                wait = 5 * (attempt + 1)
                log(f"  [RATE LIMIT] Waiting {wait}s before retry ({attempt + 1}/{retries})...")
                time.sleep(wait)
                continue
            log(f"  [ERROR] HL API error: {e}")
            return []
        except Exception as e:
            log(f"  [ERROR] HL API error: {e}")
            return []
    return []


def fetch_user_fills_by_time(
    address: str,
    start_time: int,
    end_time: int | None = None
) -> list:
    """
    Fetch all fills for a user within a time range.
    Handles pagination (max 500 per request).
    """
    all_fills = []
    current_start = start_time

    while True:
        payload = {
            "type": "userFillsByTime",
            "user": address,
            "startTime": current_start,
        }
        if end_time:
            payload["endTime"] = end_time

        fills = hl_post(payload)
        if not fills or not isinstance(fills, list):
            break

        all_fills.extend(fills)

        # If we got exactly 500, there might be more — paginate
        if len(fills) >= 500:
            last_time = fills[-1].get("time", 0)
            current_start = last_time + 1  # next ms
            time.sleep(API_DELAY)
        else:
            break

    return all_fills


def fetch_referral_data(address: str) -> dict:
    """Fetch Hyperliquid referral data for an address."""
    payload = {"type": "referral", "user": address}
    result = hl_post(payload)
    return result if isinstance(result, dict) else {}


# =============================================================================
# VOLUME CALCULATION
# =============================================================================

def calculate_notional_volume(fills: list) -> dict:
    """
    Calculate notional volume metrics from a list of fills.
    Notional volume = price × size for each fill.
    """
    if not fills:
        return {
            "total_volume": 0,
            "volume_24h": 0,
            "volume_7d": 0,
            "volume_30d": 0,
            "total_trades": 0,
            "total_fees": 0,
            "total_builder_fees": 0,
            "daily_volumes": {},
            "open_volume": 0,
            "close_volume": 0,
        }

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    ms_24h = 24 * 60 * 60 * 1000
    ms_7d = 7 * ms_24h
    ms_30d = 30 * ms_24h

    total_vol = 0
    vol_24h = 0
    vol_7d = 0
    vol_30d = 0
    total_fees = 0
    total_builder_fees = 0
    open_vol = 0
    close_vol = 0
    daily_volumes = {}

    for fill in fills:
        try:
            px = float(fill.get("px", 0))
            sz = float(fill.get("sz", 0))
            notional = px * sz
            fill_time = int(fill.get("time", 0))
            fee = float(fill.get("fee", 0))
            builder_fee = float(fill.get("builderFee", 0))
            direction = fill.get("dir", "")

            total_vol += notional
            total_fees += fee
            total_builder_fees += builder_fee

            # Track open vs close volume
            if "Open" in direction:
                open_vol += notional
            elif "Close" in direction:
                close_vol += notional

            # Time-based buckets
            age = now_ms - fill_time
            if age <= ms_24h:
                vol_24h += notional
            if age <= ms_7d:
                vol_7d += notional
            if age <= ms_30d:
                vol_30d += notional

            # Daily breakdown
            day_str = datetime.fromtimestamp(
                fill_time / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%d")
            daily_volumes[day_str] = daily_volumes.get(day_str, 0) + notional

        except (ValueError, TypeError):
            continue

    return {
        "total_volume": round(total_vol, 2),
        "volume_24h": round(vol_24h, 2),
        "volume_7d": round(vol_7d, 2),
        "volume_30d": round(vol_30d, 2),
        "total_trades": len(fills),
        "total_fees": round(total_fees, 4),
        "total_builder_fees": round(total_builder_fees, 4),
        "daily_volumes": {k: round(v, 2) for k, v in sorted(daily_volumes.items())},
        "open_volume": round(open_vol, 2),
        "close_volume": round(close_vol, 2),
    }


def filter_pear_fills(fills: list) -> list:
    """
    Filter fills to only include those executed through Pear Protocol.
    A fill has a builderFee field when executed through a builder (Pear).
    """
    pear_fills = []
    for fill in fills:
        # If builderFee exists and > 0, it went through a builder
        builder_fee = fill.get("builderFee")
        if builder_fee is not None:
            try:
                if float(builder_fee) > 0:
                    pear_fills.append(fill)
            except (ValueError, TypeError):
                pass
    return pear_fills


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_address(address: str, name: str, fetch_referral: bool = False) -> dict:
    """Process a single address: fetch fills, calculate volume, optionally get referrals."""
    log(f"  Processing {name} ({address[:10]}...)")

    # Fetch fills from 90 days ago to now
    now = datetime.now(timezone.utc)
    start_time = int((now - timedelta(days=90)).timestamp() * 1000)
    end_time = int(now.timestamp() * 1000)

    # Get all fills for this address
    all_fills = fetch_user_fills_by_time(address, start_time, end_time)
    log(f"    Total fills (all): {len(all_fills)}")
    time.sleep(API_DELAY)

    # Filter to Pear-only fills
    pear_fills = filter_pear_fills(all_fills)
    log(f"    Pear fills: {len(pear_fills)}")

    # Calculate volumes
    pear_volume = calculate_notional_volume(pear_fills)
    all_volume = calculate_notional_volume(all_fills)

    record = {
        "address": address,
        "name": name,
        "pear": pear_volume,           # Volume exclusively via Pear
        "all_hyperliquid": {            # Total HL volume (for reference)
            "total_volume": all_volume["total_volume"],
            "total_trades": all_volume["total_trades"],
        },
        "last_updated": now.isoformat(),
    }

    # Fetch referral data if ambassador
    if fetch_referral:
        time.sleep(API_DELAY)
        ref_data = fetch_referral_data(address)
        if ref_data:
            referrer_state = ref_data.get("referrerState", {})
            referrer_data = referrer_state.get("data", {})
            referral_states = referrer_data.get("referralStates", [])

            record["referral"] = {
                "source": "hyperliquid",  # Will change to "pear" when API available
                "code": referrer_data.get("code", ""),
                "total_referral_volume": sum(
                    float(r.get("cumVlm", 0)) for r in referral_states
                ),
                "referee_count": len(referral_states),
                "referees": [
                    {
                        "address": r.get("user", ""),
                        "volume": float(r.get("cumVlm", 0)),
                        "fees_rewarded": float(r.get("cumFeesRewardedToReferrer", 0)),
                        "joined": r.get("timeJoined", 0),
                    }
                    for r in referral_states
                ],
                "rewards_claimed": float(ref_data.get("claimedRewards", 0)),
                "rewards_unclaimed": float(ref_data.get("unclaimedRewards", 0)),
                "builder_rewards": float(ref_data.get("builderRewards", 0)),
            }

            # PLACEHOLDER: Pear-specific referral data
            # When Pear API is available, uncomment and add:
            # record["pear_referral"] = fetch_pear_referrals(address)

            log(f"    Referral: {record['referral']['referee_count']} referees, "
                f"vol: ${record['referral']['total_referral_volume']:,.0f}")

    return record


def process_ambassadors():
    """Process all ambassador addresses."""
    log("=" * 60)
    log("PROCESSING AMBASSADORS")
    log("=" * 60)

    df = read_google_sheet(AMBASSADORS_CSV_URL)
    if df.empty:
        log("[WARN] No ambassador data. Using sample data for testing.")
        # Sample data for testing — remove when real sheet is connected
        df = pd.DataFrame([
            {"address": "0x0000000000000000000000000000000000000000", "name": "Test Ambassador", "refcode": "TEST", "status": "active"}
        ])

    results = []
    for _, row in df.iterrows():
        address = str(row.get("address", "")).strip()
        name = str(row.get("name", "Unknown")).strip()

        if not address or address == "nan" or not address.startswith("0x") or len(address) != 42:
            if address and address != "nan":
                log(f"  [SKIP] Invalid address for {name}: {address}")
            continue

        record = process_address(address, name, fetch_referral=True)
        record["refcode"] = str(row.get("refcode", "")).strip()
        results.append(record)
        time.sleep(API_DELAY)

    return results


def process_vips():
    """Process all VIP addresses."""
    log("=" * 60)
    log("PROCESSING VIPs")
    log("=" * 60)

    df = read_google_sheet(VIPS_CSV_URL)
    if df.empty:
        log("[WARN] No VIP data. Using sample data for testing.")
        df = pd.DataFrame([
            {"address": "0x0000000000000000000000000000000000000000", "name": "Test VIP", "status": "active"}
        ])

    results = []
    for _, row in df.iterrows():
        address = str(row.get("address", "")).strip()
        name = str(row.get("name", "Unknown")).strip()

        if not address or address == "nan" or not address.startswith("0x") or len(address) != 42:
            if address and address != "nan":
                log(f"  [SKIP] Invalid address for {name}: {address}")
            continue

        record = process_address(address, name, fetch_referral=False)
        results.append(record)
        time.sleep(API_DELAY)

    return results


def save_data(data: list, filename: str):
    """Save processed data to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_DIR / filename
    with open(filepath, "w") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(data),
            "data": data,
        }, f, indent=2)
    log(f"Saved {len(data)} records to {filepath}")


def main():
    log("Pear Protocol Dashboard — Data Fetcher")
    log(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    log("")

    ambassadors = process_ambassadors()
    save_data(ambassadors, "ambassadors.json")

    log("")
    vips = process_vips()
    save_data(vips, "vips.json")

    log("")
    log("Done! Data files saved to /data directory.")


if __name__ == "__main__":
    main()
