import os
import json
import re
from bs4 import BeautifulSoup
from pathlib import Path

# Get the absolute path to the root data directory
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"


def extract_from_next_data(soup):
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        return None
    try:
        data = json.loads(script_tag.string)
        return data.get("props", {}).get("pageProps", {}).get("mutualFundsDetailData", {}).get("data", {})
    except Exception as e:
        print(f"Error parsing __NEXT_DATA__: {e}")
        return None


def _safe_get(obj, *keys, default="N/A"):
    """Safely traverse nested dicts/lists."""
    current = obj
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, None)
        elif isinstance(current, list) and isinstance(key, int) and key < len(current):
            current = current[key]
        else:
            return default
        if current is None:
            return default
    return current


# ---------------------------------------------------------------------------
# Identity & Classification helpers
# ---------------------------------------------------------------------------

def _extract_identity(next_data, soup):
    """Extract identity & classification fields."""
    info = {}
    info["short_name"] = next_data.get("short_name", "N/A")

    # AMC name from tag_links (second tag is usually AMC)
    tag_links = next_data.get("tag_links", [])
    amc_name = "N/A"
    for tag in tag_links:
        link = tag.get("link", "")
        if "/amc/" in link:
            amc_name = tag.get("name", "N/A")
            break
    info["amc_name"] = amc_name

    # Fund category from tag_links (first and third tags)
    fund_category = "N/A"
    fund_sub_category = "N/A"
    for tag in tag_links:
        link = tag.get("link", "")
        name = tag.get("name", "")
        if "/equity/" in link or "/debt/" in link or "/hybrid/" in link:
            fund_sub_category = name
        elif name in ("Equity", "Debt", "Hybrid", "Solution Oriented", "Other"):
            fund_category = name

    # If fund_category wasn't found from tags, try first tag
    if fund_category == "N/A" and tag_links:
        fund_category = tag_links[0].get("name", "N/A")

    info["fund_category"] = fund_category
    info["fund_sub_category"] = fund_sub_category

    # Fund type — Infer from is_regular_fund and URL patterns
    info["fund_type"] = "Open-ended"  # All INDMoney listed funds are open-ended
    info["plan_type"] = "Regular" if next_data.get("is_regular_fund", False) else "Direct"
    info["option_type"] = "Growth"  # INDMoney pages are typically Growth plan

    # Benchmark index variant from fund_overview
    fund_overview = next_data.get("fund_overview", {})
    overview_info = fund_overview.get("info", [])
    benchmark_full = "N/A"
    for item in overview_info:
        if item.get("name", "").lower() == "benchmark":
            benchmark_full = item.get("value", "N/A")
            break
    info["benchmark_index_name"] = benchmark_full
    # Determine TRI/PRI variant
    if "TR " in benchmark_full or "TRI" in benchmark_full or benchmark_full.endswith("TR INR"):
        info["benchmark_index_variant"] = "TRI"
    elif "PRI" in benchmark_full:
        info["benchmark_index_variant"] = "PRI"
    else:
        info["benchmark_index_variant"] = "TRI"  # Default for most SEBI benchmarks

    # ELSS detection
    about_text = ""
    about_section = next_data.get("about", {})
    if isinstance(about_section, dict):
        about_fund_list = about_section.get("about_fund", [])
        if about_fund_list:
            texts = about_fund_list[0].get("text", [])
            for t in texts:
                about_text += t.get("title", "")

    lock_in = "N/A"
    for item in overview_info:
        if "lock" in item.get("name", "").lower():
            lock_in = item.get("value", "N/A")
            break

    is_elss = "yes" if ("elss" in about_text.lower() or
                         "elss" in next_data.get("name", "").lower() or
                         "3 year" in lock_in.lower()) else "no"
    info["is_elss"] = is_elss

    # ETF / FOF detection
    name_lower = next_data.get("name", "").lower()
    info["is_etf_or_fof"] = "yes" if ("etf" in name_lower or "fund of fund" in name_lower or "fof" in name_lower) else "no"

    # Fund objective — extract from about_fund text
    info["fund_objective"] = about_text[:1000] if about_text else "N/A"

    return info


# ---------------------------------------------------------------------------
# Performance & Returns
# ---------------------------------------------------------------------------

def _extract_performance(next_data):
    """Extract expanded returns from fund_performance table."""
    perf = {}
    fund_performance = next_data.get("fund_performance", {})
    wp = fund_performance.get("widget_properties", {})
    card_data = wp.get("card_data", {})
    table = card_data.get("table", {})
    rows = table.get("rows", [])
    headers = table.get("columnHeader", [])

    # Build header map: id -> title
    header_map = {}
    for h in headers:
        header_map[h.get("id")] = h.get("title", "")

    # Extract returns for each period
    returns_data = {}
    for row in rows:
        cols = row.get("columns", [])
        if not cols:
            continue
        period = cols[0].get("title", "").strip()
        row_data = {}
        for col in cols[1:]:
            hid = col.get("headerId")
            header_title = header_map.get(hid, "")
            value = col.get("title", "N/A")
            if "This Fund" in header_title:
                row_data["fund"] = value
            elif "Avg" in header_title:
                row_data["category_avg"] = value
            elif "Best" in header_title:
                row_data["category_best"] = value
            elif "Worst" in header_title:
                row_data["category_worst"] = value
            elif "Rank" in header_title:
                row_data["category_rank"] = value
            elif hid == 3:  # Benchmark column (usually id=3)
                row_data["benchmark"] = value
        returns_data[period] = row_data

    # Map to flat fields
    period_map = {
        "1M": "1m", "3M": "3m", "6M": "6m",
        "1Y": "1y", "3Y": "3y", "5Y": "5y"
    }
    for period_label, suffix in period_map.items():
        rd = returns_data.get(period_label, {})
        perf[f"return_{suffix}"] = rd.get("fund", "N/A")
        perf[f"return_{suffix}_benchmark"] = rd.get("benchmark", "N/A")
        perf[f"return_{suffix}_category_avg"] = rd.get("category_avg", "N/A")
        perf[f"return_{suffix}_category_rank"] = rd.get("category_rank", "N/A")

    # Benchmark name from display_name
    display_name = card_data.get("display_name", "")
    if "vs. " in display_name:
        perf["benchmark"] = display_name.split("vs. ")[-1].strip()

    # Performance highlight text
    perf["performance_highlight"] = card_data.get("highlight_text", "N/A")

    return perf


# ---------------------------------------------------------------------------
# Risk Metrics from Peers table
# ---------------------------------------------------------------------------

def _extract_risk_metrics(next_data):
    """Extract Alpha, Beta, Sharpe, Sortino, Info Ratio from peers table."""
    metrics = {}
    peers = next_data.get("peers", {})
    wp = peers.get("widget_properties", {})
    card_data = wp.get("card_data", {})
    table = card_data.get("table", {})
    headers = table.get("columnHeader", [])
    rows = table.get("rows", [])

    # Build header map
    header_map = {}
    for h in headers:
        header_map[h.get("id")] = h.get("title", "")

    # First row is typically the current fund
    if rows:
        first_row = rows[0].get("columns", [])
        for col in first_row:
            hid = col.get("headerId")
            title = header_map.get(hid, "").lower()
            value = col.get("title", "N/A")
            if "alpha" in title:
                metrics["alpha_3y"] = value
            elif "beta" in title:
                metrics["beta_3y"] = value
            elif "sharpe" in title:
                metrics["sharpe_3y"] = value
            elif "sortino" in title:
                metrics["sortino_3y"] = value
            elif "info" in title:
                metrics["info_ratio_3y"] = value
            elif "aum" in title:
                metrics["aum"] = value
            elif "expense" in title:
                metrics["expense_ratio"] = value

    return metrics


# ---------------------------------------------------------------------------
# Holdings
# ---------------------------------------------------------------------------

def _extract_holdings(next_data):
    """Extract holdings data."""
    result = {}
    holdings_data = next_data.get("holdings", {})

    # Total holdings count
    holdings_count = holdings_data.get("holdings_count", [])
    total_count = 0
    count_breakdown = {}
    for hc in holdings_count:
        count = hc.get("count", 0)
        total_count += count
        name = hc.get("name", "")
        count_breakdown[name] = {"count": count, "pct": hc.get("perc", 0)}
    result["total_holdings_count"] = total_count
    result["holdings_count_breakdown"] = count_breakdown

    # Top holdings (from first holdings group, usually Equity)
    top_holdings = []
    holdings_groups = holdings_data.get("holdings", [])
    for group in holdings_groups:
        group_name = group.get("name", "")
        rows = group.get("table", {}).get("rows", [])
        for row in rows[:10]:  # Top 10
            holding = {
                "name": row.get("name", "N/A"),
                "sector": row.get("sector", "N/A"),
                "shares": row.get("current_number_of_shares", 0),
            }
            # Extract allocation % and change % from columns
            cols = row.get("columns", [])
            for col in cols:
                hid = col.get("headerId")
                if hid == 2:  # Allocation %
                    holding["allocation_pct"] = col.get("title", "N/A")
                elif hid == 4:  # Change %
                    holding["change_pct"] = col.get("title", "N/A")
            holding["asset_class"] = group_name
            top_holdings.append(holding)

    result["top_holdings"] = top_holdings[:10]  # Limit to top 10 across all groups
    return result


# ---------------------------------------------------------------------------
# Asset Allocation
# ---------------------------------------------------------------------------

def _extract_asset_allocation(next_data):
    """Extract asset allocation with market cap and credit rating breakdown."""
    aa_data = next_data.get("asset_allocation", {})
    distribution = aa_data.get("distribution", [])

    result = {"asset_allocation": []}
    for dist in distribution:
        entry = {
            "name": dist.get("name", "N/A"),
            "pct": dist.get("perc", "N/A"),
            "pct_value": dist.get("PercentageVal", 0),
        }
        # Market cap / credit rating breakdown
        mcd = dist.get("market_cap_distribution", {})
        if mcd:
            entry["breakdown_label"] = mcd.get("display_name", "")
            entry["breakdown"] = []
            for mc in mcd.get("market_cap", []):
                entry["breakdown"].append({
                    "name": mc.get("name", ""),
                    "pct": mc.get("perc", ""),
                    "value": mc.get("value", 0)
                })
        result["asset_allocation"].append(entry)

    # Extract flat market cap allocation for convenience
    for dist in distribution:
        if dist.get("name", "").lower() == "equity":
            mcd = dist.get("market_cap_distribution", {})
            cap_map = {}
            for mc in mcd.get("market_cap", []):
                key = mc.get("name", "").lower().replace(" ", "_") + "_pct"
                cap_map[key] = mc.get("perc", "N/A")
            result["market_cap_allocation"] = cap_map
            break

    if "market_cap_allocation" not in result:
        result["market_cap_allocation"] = {}

    return result


# ---------------------------------------------------------------------------
# Sector Allocation
# ---------------------------------------------------------------------------

def _extract_sector_allocation(next_data):
    """Extract sector allocation."""
    sa_data = next_data.get("sector_allocation", {})
    distribution = sa_data.get("distribution", [])

    sectors = []
    for dist in distribution:
        dist_name = dist.get("name", "")
        for sector in dist.get("sectors", []):
            sectors.append({
                "name": sector.get("name", ""),
                "pct": sector.get("perc", ""),
                "pct_value": sector.get("percValue", 0),
                "asset_class": dist_name
            })

    return {"sector_allocation": sectors}


# ---------------------------------------------------------------------------
# Fund Overview Details
# ---------------------------------------------------------------------------

def _extract_fund_overview(next_data):
    """Extract structured fields from fund_overview.info list."""
    fo = next_data.get("fund_overview", {})
    info_items = fo.get("info", [])

    result = {}
    for item in info_items:
        name = item.get("name", "").strip()
        value = item.get("value", "N/A")
        key = name.lower().replace(" ", "_").replace("/", "_")

        if "expense" in key:
            result["expense_ratio"] = value
        elif "benchmark" in key:
            result["benchmark"] = value
        elif "aum" in key:
            result["aum"] = value
        elif "inception" in key:
            result["inception_date"] = value
        elif "lumpsum" in key or "sip" in key:
            result["min_lumpsum_sip"] = value
            # Parse into separate fields
            parts = value.replace("₹", "").replace(",", "").strip().split("/")
            if len(parts) == 2:
                result["min_lumpsum_amount"] = f"₹{parts[0].strip()}"
                result["min_sip_amount"] = f"₹{parts[1].strip()}"
        elif "exit" in key:
            result["exit_load"] = value
        elif "lock" in key:
            result["lock_in"] = value
        elif "turn" in key:
            result["turnover"] = value
        elif "risk" in key:
            result["risk"] = value

    return result


# ---------------------------------------------------------------------------
# Risk Meter
# ---------------------------------------------------------------------------

def _extract_risk_meter(next_data):
    """Extract riskometer data."""
    rm = next_data.get("risk_meter", {})
    wp = rm.get("widget_properties", {})

    zone_title = wp.get("zone_title", "N/A")
    body = wp.get("body", "N/A")

    # Also set 'risk' for backward compatibility
    return {
        "riskometer_category": zone_title,
        "riskometer_body": body,
        "risk": zone_title,
    }


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def _extract_ranking(next_data):
    """Extract INDmoney ranking data."""
    ranking = next_data.get("ranking", {})
    wp = ranking.get("widget_properties", {})
    card_data = wp.get("card_data", {})

    result = {
        "indmoney_rank": card_data.get("rank", "N/A"),
        "total_funds_in_category": card_data.get("total_funds", "N/A"),
        "ranking_info": card_data.get("rankingInfo", "N/A"),
    }

    # Scores
    scores = {}
    for r in card_data.get("ranking", []):
        param = r.get("parameter", "").lower().replace(" ", "_")
        scores[param] = r.get("rating", "N/A")
    result["ranking_scores"] = scores

    # Pros and Cons
    traits = card_data.get("traits", [])
    pros = []
    cons = []
    for trait in traits:
        header = trait.get("header", "").lower()
        items = [r.get("title", "") for r in trait.get("rows", [])]
        if "pro" in header:
            pros = items
        elif "con" in header:
            cons = items
    result["ranking_pros"] = pros
    result["ranking_cons"] = cons

    return result


# ---------------------------------------------------------------------------
# About / Fund Managers / AMC
# ---------------------------------------------------------------------------

def _extract_about_and_managers(next_data, soup):
    """Extract about text, fund manager details, AMC info."""
    result = {}

    # About text from DOM (existing approach, preserved)
    about_div = soup.find("div", id="about")
    result["about"] = about_div.get_text(separator=" ").strip() if about_div else ""

    # Fund managers — structured from __NEXT_DATA__
    about_section = next_data.get("about", {})
    managers_data = _safe_get(about_section, "managers", "widget_properties", "card_data", "managers_info", default=[])

    managers_detail = []
    manager_names = []
    if isinstance(managers_data, list):
        for m in managers_data:
            name = m.get("title", "")
            subtitle = m.get("subtitle", "")
            managers_detail.append({"name": name, "subtitle": subtitle})
            if name:
                manager_names.append(name)

    result["fund_managers"] = ", ".join(manager_names) if manager_names else "N/A"
    result["fund_managers_detail"] = managers_detail

    # AMC info
    amc = about_section.get("amc", {}) if isinstance(about_section, dict) else {}
    result["amc_page_url"] = amc.get("link", "N/A")

    # AUM change history from about.highlights.table
    highlights = about_section.get("highlights", {}) if isinstance(about_section, dict) else {}
    aum_table = highlights.get("table", {})
    aum_history = {}
    col_headers = aum_table.get("columnHeader", [])
    rows = aum_table.get("rows", [])

    # Build column header map
    month_map = {}
    for ch in col_headers:
        if ch.get("id", 0) >= 2:  # Skip "Parameters" column
            month_map[ch["id"]] = ch.get("title", "")

    for row in rows:
        cols = row.get("columns", [])
        param_name = cols[0].get("title", "") if cols else ""
        if "aum" in param_name.lower():
            for col in cols[1:]:
                hid = col.get("headerId")
                month = month_map.get(hid, "")
                if month:
                    aum_history[month] = col.get("title", "N/A")

    result["aum_history"] = aum_history

    # AUM change highlights
    highlights_list = highlights.get("highlights", [])
    if isinstance(highlights_list, list):
        aum_add_info = [h.get("text", "") for h in highlights_list if isinstance(h, dict)]
    else:
        aum_add_info = []
    result["aum_change_summary"] = highlights.get("add_info", aum_add_info)

    return result


# ---------------------------------------------------------------------------
# NAV data
# ---------------------------------------------------------------------------

def _extract_nav_data(next_data):
    """Extract NAV-related fields."""
    return {
        "nav": next_data.get("nav", "N/A"),
        "nav_date": next_data.get("nav_date", "N/A"),
        "nav_text": next_data.get("nav_text", "N/A"),
        "nav_currency": "INR",
        "one_day_change_pct": next_data.get("one_day_change", "N/A"),
        "inception_return": next_data.get("inception_return", "N/A"),
    }


# ---------------------------------------------------------------------------
# Main parse function
# ---------------------------------------------------------------------------

def parse_fund_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    next_data = extract_from_next_data(soup)

    if not next_data:
        print(f"Warning: __NEXT_DATA__ not found in {file_path}. Falling back to basic parsing.")
        return {"error": "Structured data not found"}

    fund_data = {}

    # ---- Existing fields (preserved) ----
    fund_data["fund_name"] = next_data.get("name", "N/A")

    # ---- NAV & Pricing ----
    fund_data.update(_extract_nav_data(next_data))

    # ---- Identity & Classification ----
    fund_data.update(_extract_identity(next_data, soup))

    # ---- Fund Overview (expense ratio, AUM, inception, etc.) ----
    fund_data.update(_extract_fund_overview(next_data))

    # ---- Returns & Performance ----
    fund_data.update(_extract_performance(next_data))

    # ---- Risk Metrics ----
    fund_data.update(_extract_risk_metrics(next_data))

    # ---- Holdings ----
    fund_data.update(_extract_holdings(next_data))

    # ---- Asset Allocation ----
    fund_data.update(_extract_asset_allocation(next_data))

    # ---- Sector Allocation ----
    fund_data.update(_extract_sector_allocation(next_data))

    # ---- Risk Meter ----
    fund_data.update(_extract_risk_meter(next_data))

    # ---- Ranking ----
    fund_data.update(_extract_ranking(next_data))

    # ---- About, Fund Managers, AMC ----
    fund_data.update(_extract_about_and_managers(next_data, soup))

    # ---- Fields set to N/A for future enrichment ----
    placeholders = [
        "scheme_code", "isin_growth", "isin_div_reinvestment",
        "return_ytd", "return_10y", "return_since_inception",
        "sip_xirr_1y", "sip_xirr_3y", "sip_xirr_5y", "sip_xirr_10y",
        "rolling_returns", "standard_deviation",
        "nav_52w_high", "nav_52w_low",
        "portfolio_overlap_pct",
        "expense_ratio_regular",
        "min_additional_lumpsum", "min_sip_installments", "min_redemption_amount",
        "stamp_duty", "stt_applicable",
        "factsheet_url", "sid_url", "sai_url", "kim_url", "amfi_page_url",
        "number_of_folios",
        "country_allocation",
        "historical_nav",
    ]
    for key in placeholders:
        if key not in fund_data:
            fund_data[key] = None

    return fund_data


def main():
    if not os.path.exists(PROCESSED_DATA_DIR):
        os.makedirs(PROCESSED_DATA_DIR)

    for filename in os.listdir(RAW_DATA_DIR):
        if filename.endswith(".html"):
            file_path = os.path.join(RAW_DATA_DIR, filename)
            print(f"Parsing {filename}...")
            try:
                data = parse_fund_html(file_path)
                output_path = os.path.join(PROCESSED_DATA_DIR, filename.replace(".html", ".json"))
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"Successfully processed {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
