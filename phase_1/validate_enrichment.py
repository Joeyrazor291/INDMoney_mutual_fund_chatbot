import json
import os
import re

data_dir = "data/processed"
required_old = ["fund_name", "nav", "nav_date", "aum", "expense_ratio", "benchmark", "inception_date", "exit_load", "lock_in", "turnover", "risk", "about", "fund_managers"]
required_new = ["short_name", "amc_name", "fund_category", "plan_type", "one_day_change_pct", "inception_return", "return_1m", "return_3m", "return_6m", "return_1y", "return_3y", "return_5y", "alpha_3y", "beta_3y", "sharpe_3y", "sortino_3y", "top_holdings", "asset_allocation", "sector_allocation", "market_cap_allocation", "riskometer_category", "indmoney_rank", "ranking_scores", "fund_managers_detail", "scheme_code", "isin_growth", "historical_nav", "nav_52w_high", "nav_52w_low", "taxation", "sip_mechanics", "redemption_details", "guardrails", "sebi_investment_mandate"]

# PII patterns
pii_patterns = [
    r"\b[A-Z]{5}\d{4}[A-Z]\b",
    r"\b\d{12}\b",
    r"\b[\w.+-]+@[\w-]+\.[\w.]+\b",
]

print("=== VALIDATION REPORT ===\n")
for f in sorted(os.listdir(data_dir)):
    if not f.endswith(".json"):
        continue
    with open(os.path.join(data_dir, f), "r", encoding="utf-8") as fh:
        data = json.load(fh)

    name = data.get("fund_name", "UNKNOWN")
    print(f"--- {name} ({f}) ---")

    missing_old = [k for k in required_old if k not in data or data[k] in (None, "", "N/A")]
    if missing_old:
        print(f"  WARN: Missing old fields: {missing_old}")
    else:
        print(f"  OK: All {len(required_old)} old fields present")

    missing_new = [k for k in required_new if k not in data or data[k] is None]
    present_new = len(required_new) - len(missing_new)
    print(f"  NEW: {present_new}/{len(required_new)} new fields present")
    if missing_new:
        print(f"  Missing new: {missing_new}")

    th = data.get("top_holdings", [])
    total_count = data.get("total_holdings_count", 0)
    print(f"  Holdings: {len(th)} entries, Total: {total_count}")

    sa = data.get("sector_allocation", [])
    print(f"  Sectors: {len(sa)} entries")

    hn = data.get("historical_nav", [])
    print(f"  Historical NAV: {len(hn)} entries")

    high = data.get("nav_52w_high", "N/A")
    low = data.get("nav_52w_low", "N/A")
    print(f"  52W High: {high}, Low: {low}")

    sc = data.get("scheme_code")
    isin = data.get("isin_growth")
    print(f"  Scheme Code: {sc}, ISIN: {isin}")

    text = json.dumps(data)
    pii_found = False
    for pat in pii_patterns:
        matches = re.findall(pat, text)
        if matches and len(matches) > 2:
            print(f"  WARN: Potential PII pattern found")
            pii_found = True
    if not pii_found:
        print(f"  OK: No PII detected")

    fsize = os.path.getsize(os.path.join(data_dir, f))
    print(f"  File size: {fsize / 1024:.1f} KB")
    
    # Key spot checks
    tax = data.get("taxation", {})
    sip = data.get("sip_mechanics", {})
    print(f"  Tax Category: {tax.get('fund_tax_category', 'N/A')}, 80C: {tax.get('section_80c_eligible', 'N/A')}")
    print(f"  SIP Available: {sip.get('sip_available', 'N/A')}")
    print()
