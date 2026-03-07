"""
MFAPI Data Fetcher
Fetches scheme metadata and historical NAV data from api.mfapi.in
"""
import json
import os
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

# Mapping of fund slugs to AMFI scheme codes
SCHEME_CODES = {
    "hdfc-flexi-cap": 118955,
    "hdfc-mid-cap": 118989,
    "absl-quant": 152684,
    "absl-elss": 119544,
    "edelweiss-nifty-next-50": 150899,
}

# Number of days of historical NAV to store
NAV_HISTORY_DAYS = 365


def fetch_mfapi_data(scheme_code):
    """Fetch data from MFAPI for a given scheme code."""
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"  Error fetching MFAPI data for scheme {scheme_code}: {e}")
        return None


def enrich_with_mfapi(fund_slug, fund_data):
    """Enrich a fund's JSON data with MFAPI metadata and historical NAV."""
    scheme_code = SCHEME_CODES.get(fund_slug)
    if not scheme_code:
        print(f"  No MFAPI scheme code for {fund_slug}, skipping.")
        return fund_data

    print(f"  Fetching MFAPI data for {fund_slug} (scheme code: {scheme_code})...")
    api_data = fetch_mfapi_data(scheme_code)
    if not api_data:
        return fund_data

    meta = api_data.get("meta", {})
    nav_history = api_data.get("data", [])

    # Merge scheme metadata
    fund_data["scheme_code"] = meta.get("scheme_code", None)
    fund_data["isin_growth"] = meta.get("isin_growth", None)
    fund_data["isin_div_reinvestment"] = meta.get("isin_div_reinvestment", None)
    fund_data["mfapi_fund_house"] = meta.get("fund_house", None)
    fund_data["mfapi_scheme_type"] = meta.get("scheme_type", None)
    fund_data["mfapi_scheme_category"] = meta.get("scheme_category", None)
    fund_data["mfapi_scheme_name"] = meta.get("scheme_name", None)

    # Construct AMFI page URL
    if scheme_code:
        fund_data["amfi_page_url"] = f"https://www.amfiindia.com/net-asset-value/mutual-fund-scheme?SchemeCode={scheme_code}"

    # Store last N days of historical NAV
    cutoff = datetime.now() - timedelta(days=NAV_HISTORY_DAYS)
    historical_nav = []
    for entry in nav_history:
        try:
            date_str = entry.get("date", "")
            nav_val = entry.get("nav", "")
            dt = datetime.strptime(date_str, "%d-%m-%Y")
            if dt >= cutoff:
                historical_nav.append({"date": date_str, "nav": nav_val})
        except (ValueError, TypeError):
            continue

    fund_data["historical_nav"] = historical_nav

    # Compute 52-week high/low from historical NAV
    if historical_nav:
        nav_values = []
        for h in historical_nav:
            try:
                nav_values.append(float(h["nav"]))
            except (ValueError, TypeError):
                continue
        if nav_values:
            fund_data["nav_52w_high"] = f"₹{max(nav_values):.2f}"
            fund_data["nav_52w_low"] = f"₹{min(nav_values):.2f}"

    # Compute previous day NAV
    if len(nav_history) >= 2:
        fund_data["previous_day_nav"] = nav_history[1].get("nav", None)
        try:
            current_nav = float(nav_history[0].get("nav", 0))
            prev_nav = float(nav_history[1].get("nav", 0))
            if prev_nav > 0:
                change_abs = current_nav - prev_nav
                change_pct = (change_abs / prev_nav) * 100
                fund_data["nav_change_absolute"] = f"₹{change_abs:.2f}"
                fund_data["nav_change_pct"] = f"{change_pct:.2f}%"
        except (ValueError, TypeError):
            pass

    print(f"  MFAPI enrichment complete: {len(historical_nav)} NAV entries, scheme={scheme_code}")
    return fund_data


def main():
    """Enrich all processed JSON files with MFAPI data."""
    print("=" * 40)
    print("MFAPI Data Enrichment")
    print("=" * 40)

    for json_file in sorted(PROCESSED_DATA_DIR.glob("*.json")):
        fund_slug = json_file.stem
        print(f"\nProcessing {fund_slug}...")

        with open(json_file, "r", encoding="utf-8") as f:
            fund_data = json.load(f)

        fund_data = enrich_with_mfapi(fund_slug, fund_data)

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(fund_data, f, indent=4, ensure_ascii=False)

        print(f"  Saved enriched data to {json_file.name}")

    print("\nMFAPI enrichment complete!")


if __name__ == "__main__":
    main()
