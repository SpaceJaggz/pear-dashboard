"""
Pear Protocol Dashboard — Data Fetcher v2.2
============================================
Uses Pear Protocol's official API for accurate volume data.
Includes retry logic for referral API timeouts and partial response detection.

API endpoints:
  - Volume:   https://hl-v2.pearprotocol.io/public-stats/address?addresses=0x...
  - Referral: https://api.pearprotocol.io/v1/stats/referral?address=0x...

Usage:
    python3 fetch_data.py
"""

import os
import io
import json
import time
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

# Google Sheets "Publish to web" CSV URLs
AMBASSADORS_CSV_URL = os.environ.get(
    "AMBASSADORS_CSV_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQwS66TXQGEBmbnaBBLikcOnWbAe6_sg2zgBx1FpqVdRptOfhDjB076bCAz4In3CPKEF05pUtcwrTG8/pub?gid=0&single=true&output=csv"
)
VIPS_CSV_URL = os.environ.get(
    "VIPS_CSV_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQwS66TXQGEBmbnaBBLikcOnWbAe6_sg2zgBx1FpqVdRptOfhDjB076bCAz4In3CPKEF05pUtcwrTG8/pub?gid=2090993430&single=true&output=csv"
)

# Pear Protocol API endpoints
PEAR_VOLUME_API = "https://hl-v2.pearprotocol.io/public-stats/address"
PEAR_REFERRAL_API = "https://api.pearprotocol.io/v1/stats/referral"

# Output directory
DATA_DIR = Path(__file__).parent / "data"

# Rate limit delay between API calls (seconds)
API_DELAY = 1.0


def log(msg: str):
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
        df.columns = [c.strip().lower() for c in df.columns]
        if "status" in df.columns:
            df = df[df["status"].str.strip().str.lower() == "active"]
        log(f"  Found {len(df)} active addresses")
        return df
    except Exception as e:
        log(f"  [ERROR] Failed to read sheet: {e}")
        return pd.DataFrame()


# =============================================================================
# PEAR PROTOCOL API
# =============================================================================

def fetch_pear_volumes(addresses: list[str]) -> dict:
    """
    Fetch volume data for multiple addresses in one call.
    Returns dict: {address: {totalVolume, totalExternalFeePaid, totalBuilderFeePaid}}
    Batches requests in groups of 10 (API limit).
    """
    if not addresses:
        return {}

    BATCH_SIZE = 10
    result = {}

    log(f"  Fetching Pear volumes for {len(addresses)} addresses (batched by {BATCH_SIZE})...")

    for i in range(0, len(addresses), BATCH_SIZE):
        batch = addresses[i:i + BATCH_SIZE]
        addr_str = ",".join(batch)
        url = f"{PEAR_VOLUME_API}?addresses={addr_str}"

        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(addresses) + BATCH_SIZE - 1) // BATCH_SIZE

        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("data", []):
                addr = item.get("address", "").lower()
                result[addr] = {
                    "total_volume": float(item.get("totalVolume", 0)),
                    "total_fees": float(item.get("totalExternalFeePaid", 0)),
                    "total_builder_fees": float(item.get("totalBuilderFeePaid", 0)),
                }
            log(f"    Batch {batch_num}/{total_batches}: got {len(batch)} addresses")

        except Exception as e:
            log(f"    [ERROR] Batch {batch_num}/{total_batches} failed: {e}")

        # Small delay between batches to avoid rate limits
        if i + BATCH_SIZE < len(addresses):
            time.sleep(1.0)

    log(f"  Got volume data for {len(result)} addresses total")
    return result


def fetch_pear_referral(address: str, retries: int = 5) -> dict:
    """
    Fetch referral data for a single address with retry on timeout or partial response.

    Partial response detection:
      - If payload is missing or malformed → retry
      - If totalReferees > 0 but total volume = 0 → partial data, retry
      - If totalReferees = 0 and volume = 0 → valid (no referral activity yet)

    Returns dict with totalReferees, totalVolume (HL + Intent combined).
    """
    url = f"{PEAR_REFERRAL_API}?address={address}"

    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=180)
            resp.raise_for_status()
            data = resp.json()

            # Validate payload structure
            payload = data.get("payload", None)
            if payload is None or not isinstance(payload, dict):
                raise ValueError("Empty or malformed payload")

            total_referees = int(payload.get("totalReferees", 0))
            hl_volume = float(payload.get("totalHyperliquidVolume", 0))
            intent_volume = float(payload.get("totalIntentVolume", 0))
            total_ref_volume = hl_volume + intent_volume

            # Detect partial response: has referees but volume is 0
            if total_referees > 0 and total_ref_volume == 0:
                raise ValueError(f"Partial data detected: {total_referees} referees but volume=0")

            return {
                "total_referees": total_referees,
                "total_referral_volume": round(total_ref_volume, 2),
                "hl_referral_volume": round(hl_volume, 2),
                "intent_referral_volume": round(intent_volume, 2),
            }

        except Exception as e:
            if attempt < retries - 1:
                wait = 15 * (attempt + 1)
                log(f"    [RETRY] Referral API issue for {address[:10]}... — {e} — waiting {wait}s ({attempt + 1}/{retries})")
                time.sleep(wait)
            else:
                log(f"  [ERROR] Pear referral API failed after {retries} attempts for {address[:10]}...: {e}")
                return {
                    "total_referees": 0,
                    "total_referral_volume": 0,
                    "hl_referral_volume": 0,
                    "intent_referral_volume": 0,
                }

    return {"total_referees": 0, "total_referral_volume": 0, "hl_referral_volume": 0, "intent_referral_volume": 0}


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_ambassadors():
    """Process all ambassador addresses."""
    log("=" * 60)
    log("PROCESSING AMBASSADORS")
    log("=" * 60)

    df = read_google_sheet(AMBASSADORS_CSV_URL)
    if df.empty:
        log("[WARN] No ambassador data found.")
        return []

    records = []
    for _, row in df.iterrows():
        address = str(row.get("address", "")).strip()
        name = str(row.get("name", "Unknown")).strip()
        refcode = str(row.get("refcode", "")).strip()

        # Read referral fee paid from sheet (column E), default 0
        try:
            ref_fee = float(row.get("referral fee paid", 0) or 0)
        except (ValueError, TypeError):
            ref_fee = 0.0

        if not address or address == "nan" or not address.startswith("0x") or len(address) != 42:
            continue

        records.append({
            "address": address,
            "name": name,
            "refcode": refcode if refcode != "nan" else "",
            "referral_fee_paid": round(ref_fee, 2),
        })

    if not records:
        log("[WARN] No valid addresses found.")
        return []

    # Fetch volumes in batch
    all_addresses = [r["address"] for r in records]
    volumes = fetch_pear_volumes(all_addresses)
    time.sleep(API_DELAY)

    # Fetch referrals per address (with retry and partial detection)
    results = []
    for r in records:
        addr_lower = r["address"].lower()
        vol_data = volumes.get(addr_lower, {
            "total_volume": 0, "total_fees": 0, "total_builder_fees": 0
        })

        log(f"  {r['name']}: vol=${vol_data['total_volume']:,.0f}, fetching referral...")
        ref_data = fetch_pear_referral(r["address"])
        time.sleep(API_DELAY)

        log(f"    Referral: {ref_data['total_referees']} referees, vol=${ref_data['total_referral_volume']:,.0f}")

        results.append({
            "address": r["address"],
            "name": r["name"],
            "refcode": r["refcode"],
            "pear": {
                "total_volume": round(vol_data["total_volume"], 2),
                "total_fees": round(vol_data["total_fees"], 4),
                "total_builder_fees": round(vol_data["total_builder_fees"], 4),
            },
            "referral": {
                "total_referees": ref_data["total_referees"],
                "total_referral_volume": ref_data["total_referral_volume"],
                "referral_fee_paid": r["referral_fee_paid"],
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
        })

    return results


def process_vips():
    """Process all VIP addresses."""
    log("=" * 60)
    log("PROCESSING VIPs")
    log("=" * 60)

    df = read_google_sheet(VIPS_CSV_URL)
    if df.empty:
        log("[WARN] No VIP data found.")
        return []

    records = []
    for _, row in df.iterrows():
        address = str(row.get("address", "")).strip()
        name = str(row.get("name", "Unknown")).strip()

        if not address or address == "nan" or not address.startswith("0x") or len(address) != 42:
            continue

        records.append({"address": address, "name": name})

    if not records:
        log("[WARN] No valid addresses found.")
        return []

    all_addresses = [r["address"] for r in records]
    volumes = fetch_pear_volumes(all_addresses)

    results = []
    for r in records:
        addr_lower = r["address"].lower()
        vol_data = volumes.get(addr_lower, {
            "total_volume": 0, "total_fees": 0, "total_builder_fees": 0
        })

        log(f"  {r['name']}: vol=${vol_data['total_volume']:,.0f}")

        results.append({
            "address": r["address"],
            "name": r["name"],
            "pear": {
                "total_volume": round(vol_data["total_volume"], 2),
                "total_fees": round(vol_data["total_fees"], 4),
                "total_builder_fees": round(vol_data["total_builder_fees"], 4),
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
        })

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
    log("Pear Protocol Dashboard — Data Fetcher v2.2")
    log(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    log("Using Pear Protocol API for accurate volume data")
    log("")

    ambassadors = process_ambassadors()
    save_data(ambassadors, "ambassadors.json")

    log("")
    vips = process_vips()
    save_data(vips, "vips.json")

    log("")
    log("Done!")


if __name__ == "__main__":
    main()
