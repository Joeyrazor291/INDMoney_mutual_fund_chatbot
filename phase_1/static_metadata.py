"""
Static Metadata Enricher
Adds rule-based metadata that can be derived from existing fund data:
- Taxation metadata
- SIP mechanics (defaults)
- Lock-in & redemption details
- Guardrail metadata for chatbot safety
- Document URL templates
"""
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"


# ---------------------------------------------------------------------------
# Taxation Rules
# ---------------------------------------------------------------------------

def _derive_taxation(fund_data):
    """Derive tax treatment based on fund type/category."""
    is_elss = fund_data.get("is_elss", "no") == "yes"
    fund_category = (fund_data.get("fund_category", "") or "").lower()
    fund_sub_category = (fund_data.get("fund_sub_category", "") or "").lower()
    name = (fund_data.get("fund_name", "") or "").lower()

    # Determine if equity-oriented
    is_equity = ("equity" in fund_category or
                 "elss" in name or
                 "flexi" in fund_sub_category or
                 "mid cap" in fund_sub_category or
                 "large cap" in fund_sub_category or
                 "small cap" in fund_sub_category or
                 "index" in name or
                 "quant" in name)

    tax = {}
    if is_equity:
        tax["fund_tax_category"] = "Equity"
        tax["stcg_tax_rate"] = "20%"
        tax["stcg_holding_period"] = "Less than 12 months"
        tax["ltcg_tax_rate"] = "12.5%"
        tax["ltcg_holding_period"] = "More than 12 months"
        tax["ltcg_exemption_limit"] = "₹1.25 lakh per financial year"
        tax["indexation_benefit"] = "No"
        tax["dividend_tax_treatment"] = "Taxed at investor's income tax slab rate"
    else:
        tax["fund_tax_category"] = "Debt"
        tax["stcg_tax_rate"] = "At investor's income tax slab rate"
        tax["stcg_holding_period"] = "Less than 24 months"
        tax["ltcg_tax_rate"] = "12.5%"
        tax["ltcg_holding_period"] = "More than 24 months"
        tax["ltcg_exemption_limit"] = "No exemption"
        tax["indexation_benefit"] = "No (removed from April 2023)"
        tax["dividend_tax_treatment"] = "Taxed at investor's income tax slab rate"

    tax["section_80c_eligible"] = "Yes" if is_elss else "No"
    tax["stt_applicable"] = "Yes" if is_equity else "No"
    tax["stamp_duty"] = "0.005%"

    return tax


# ---------------------------------------------------------------------------
# SIP Mechanics
# ---------------------------------------------------------------------------

def _derive_sip_mechanics(fund_data):
    """Derive SIP mechanics — standard defaults for open-ended equity funds."""
    is_etf = fund_data.get("is_etf_or_fof", "no") == "yes"
    fund_type = fund_data.get("fund_type", "Open-ended")

    sip = {}
    if is_etf or fund_type == "Close-ended":
        sip["sip_available"] = "No"
        sip["sip_frequencies"] = []
        sip["sip_dates"] = []
    else:
        sip["sip_available"] = "Yes"
        sip["sip_frequencies"] = ["Monthly", "Quarterly"]
        sip["sip_dates"] = [1, 5, 10, 15, 20, 25]
        sip["sip_min_amount"] = fund_data.get("min_sip_amount", "N/A")
        sip["sip_min_installments"] = 6  # Standard across most AMCs
        sip["sip_pause_facility"] = "Yes"
        sip["sip_step_up_facility"] = "Yes"
        sip["perpetual_sip"] = "Yes"

    return sip


# ---------------------------------------------------------------------------
# Lock-in & Redemption
# ---------------------------------------------------------------------------

def _derive_redemption_details(fund_data):
    """Derive redemption details from existing lock-in and fund type info."""
    is_elss = fund_data.get("is_elss", "no") == "yes"
    is_equity = (fund_data.get("fund_category", "") or "").lower() == "equity"

    redemption = {}
    redemption["lock_in_period"] = "3 years" if is_elss else fund_data.get("lock_in", "Nil")
    redemption["partial_redemption_allowed"] = "Yes (after lock-in for ELSS)" if is_elss else "Yes"

    # Processing time based on fund category
    if is_equity:
        redemption["redemption_processing_time"] = "T+2 business days"
    else:
        redemption["redemption_processing_time"] = "T+1 business days"

    redemption["cutoff_time_purchase"] = "3:00 PM (for same-day NAV)"
    redemption["cutoff_time_redemption"] = "3:00 PM (for same-day NAV)"
    redemption["settlement_type"] = "Direct credit to registered bank account"
    redemption["redemption_during_market_hours"] = "End-of-day NAV applicable"
    redemption["units_pledgeable"] = "Yes (subject to AMC terms)"

    # Parse exit load structure
    exit_load_raw = fund_data.get("exit_load", "N/A")
    exit_load_structure = {"raw": exit_load_raw}
    if exit_load_raw and exit_load_raw not in ("N/A", "0%", "Nil"):
        try:
            pct = float(exit_load_raw.replace("%", "").strip())
            exit_load_structure["pct"] = f"{pct}%"
            exit_load_structure["window"] = "Within 1 year of allotment"
            exit_load_structure["nil_beyond"] = "Yes, nil after 1 year"
            exit_load_structure["special_conditions"] = "Up to 10% of units can be redeemed without exit load within 1 year"
        except ValueError:
            pass
    elif exit_load_raw in ("0%", "Nil"):
        exit_load_structure["pct"] = "0%"
        exit_load_structure["window"] = "N/A"
        exit_load_structure["nil_beyond"] = "Yes"
        exit_load_structure["special_conditions"] = "No exit load applicable"

    redemption["exit_load_structure"] = exit_load_structure

    return redemption


# ---------------------------------------------------------------------------
# Guardrail Metadata
# ---------------------------------------------------------------------------

def _derive_guardrails(fund_data):
    """Derive chatbot safety guardrail metadata."""
    risk_label = fund_data.get("riskometer_category",
                                fund_data.get("risk", "N/A"))

    return {
        "guardrail_flags": {
            "is_performance_question": "Respond with factual data only, no personal opinion or recommendation.",
            "is_comparison_question": "Surface data side-by-side for comparison. Do not recommend one fund over another.",
            "is_advisory_question": "This appears to be an investment advisory question. As per SEBI regulations, we cannot provide personalized investment advice. Please consult a SEBI-registered investment advisor.",
            "contains_pii": "PII detected (PAN/Aadhaar/phone/email). This data will NOT be processed or stored.",
        },
        "disclaimer_text": (
            "Mutual fund investments are subject to market risks. "
            "Read all scheme-related documents carefully before investing. "
            "Past performance is not indicative of future results. "
            "The information provided is for educational purposes only and should not be "
            "construed as investment advice."
        ),
        "sebi_riskometer_label": risk_label,
    }


# ---------------------------------------------------------------------------
# Main enrichment
# ---------------------------------------------------------------------------

def enrich_with_static_metadata(fund_data):
    """Add all static/derived metadata to a fund data dict."""
    # Taxation
    fund_data["taxation"] = _derive_taxation(fund_data)

    # SIP Mechanics
    fund_data["sip_mechanics"] = _derive_sip_mechanics(fund_data)

    # Lock-in & Redemption
    fund_data["redemption_details"] = _derive_redemption_details(fund_data)

    # Guardrails
    fund_data["guardrails"] = _derive_guardrails(fund_data)

    # SEBI investment mandate (derived from sub-category)
    sub_cat = (fund_data.get("fund_sub_category", "") or "").lower()
    mandates = {
        "flexi cap": "Minimum 65% in equity across market capitalizations",
        "mid cap": "Minimum 65% in mid-cap stocks (101st to 250th by market cap)",
        "large cap": "Minimum 80% in large-cap stocks (top 100 by market cap)",
        "small cap": "Minimum 65% in small-cap stocks (251st and beyond by market cap)",
        "elss": "Minimum 80% in equity with 3-year lock-in (tax saving under Section 80C)",
        "index": "Replicates the composition of the benchmark index",
    }
    mandate = "N/A"
    for key, val in mandates.items():
        if key in sub_cat or key in (fund_data.get("fund_name", "") or "").lower():
            mandate = val
            break
    fund_data["sebi_investment_mandate"] = mandate

    return fund_data


def main():
    """Enrich all processed JSON files with static metadata."""
    print("=" * 40)
    print("Static Metadata Enrichment")
    print("=" * 40)

    for json_file in sorted(PROCESSED_DATA_DIR.glob("*.json")):
        fund_slug = json_file.stem
        print(f"Enriching {fund_slug} with static metadata...")

        with open(json_file, "r", encoding="utf-8") as f:
            fund_data = json.load(f)

        fund_data = enrich_with_static_metadata(fund_data)

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(fund_data, f, indent=4, ensure_ascii=False)

        print(f"  Done: {json_file.name}")

    print("\nStatic metadata enrichment complete!")


if __name__ == "__main__":
    main()
