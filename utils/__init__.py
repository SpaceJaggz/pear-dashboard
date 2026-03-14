"""
Shared utilities for the Pear Protocol Dashboard.
"""
import json
from pathlib import Path
from datetime import datetime


DATA_DIR = Path(__file__).parent.parent / "data"


def load_data(filename: str) -> dict:
    """Load JSON data file."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return {"generated_at": "", "count": 0, "data": []}
    with open(filepath) as f:
        return json.load(f)


def format_volume(value: float) -> str:
    """Format volume as human-readable string."""
    if value >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:,.1f}K"
    else:
        return f"${value:,.2f}"


def format_number(value: float) -> str:
    """Format a number with commas."""
    if isinstance(value, float):
        return f"{value:,.2f}"
    return f"{value:,}"


def short_address(address: str) -> str:
    """Shorten an address for display: 0x1234...5678"""
    if len(address) > 12:
        return f"{address[:6]}...{address[-4:]}"
    return address


def parse_timestamp(ts: str | int) -> str:
    """Parse timestamp to readable date string."""
    try:
        if isinstance(ts, int):
            dt = datetime.fromtimestamp(ts / 1000)
        else:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return str(ts)
