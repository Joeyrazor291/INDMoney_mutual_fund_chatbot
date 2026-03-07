import json
import os
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
VECTORSTORE_DIR = BASE_DIR / "data" / "vectorstore"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def create_fund_chunks(fund_data, fund_slug_param=None):
    """
    Creates multiple documents (chunks) for a fund:
    1. A summary chunk with all key facts.
    2. Small focused chunks for each specific fact.
    3. Holdings chunk for portfolio composition.
    4. Sector/asset allocation chunks.
    5. Risk metrics chunk.
    6. Returns chunk with benchmark comparison.
    7. Tax & costs chunk.
    8. SIP mechanics chunk.
    9. Fund manager detail chunk.
    10. Split chunks for the 'About' section.
    """
    # The original instruction mentioned `process_and_store` and `filepath`,
    # but the provided code snippet for the change is within `create_fund_chunks`
    # and introduces `filepath` which is not an argument to this function.
    # To make the change syntactically correct and faithful to the provided snippet,
    # I will assume `fund_slug` should be derived from `fund_name` as a fallback
    # if `filepath` is not available, or that `filepath` would be passed if this
    # function were called from `process_and_store`.
    # Given the context, I'll apply the `fund_slug` and `fund_name` logic as provided,
    # but will use the existing `fund_name` to derive `fund_slug` to avoid an undefined `filepath`.
    # The provided snippet also had a syntax error in the `fund_name` assignment, which is corrected.

    # Original lines:
    # fund_name = fund_data.get("fund_name", "Unknown Fund")
    # fund_slug = fund_data.get("fund_name", "Unknown").lower().replace(" ", "-")

    # Applying the spirit of the change, assuming `fund_slug` is derived from `fund_name`
    # and correcting the syntax error in the provided snippet.
    fund_name = fund_data.get("fund_name", "Unknown Fund")
    fund_slug = fund_slug_param or fund_name.lower().replace(" ", "-")
    
    chunks = []
    
    # ---- 1. THE SUMMARY CHUNK (DENSE FACTS) ----
    summary_content = f"""
Mutual Fund Name: {fund_name}
Short Name: {fund_data.get('short_name', 'N/A')}
AMC: {fund_data.get('amc_name', 'N/A')}
Category: {fund_data.get('fund_category', 'N/A')} - {fund_data.get('fund_sub_category', 'N/A')}
Plan: {fund_data.get('plan_type', 'N/A')} {fund_data.get('option_type', 'N/A')}
Latest NAV: {fund_data.get('nav', 'N/A')} as of {fund_data.get('nav_date', 'N/A')}
1-Day Change: {fund_data.get('one_day_change_pct', 'N/A')}%
Returns: 1M: {fund_data.get('return_1m', 'N/A')}, 3M: {fund_data.get('return_3m', 'N/A')}, 6M: {fund_data.get('return_6m', 'N/A')}, 1Y: {fund_data.get('return_1y', 'N/A')}, 3Y: {fund_data.get('return_3y', 'N/A')}, 5Y: {fund_data.get('return_5y', 'N/A')}
Since Inception Return (CAGR): {fund_data.get('inception_return', 'N/A')}%
Expense Ratio: {fund_data.get('expense_ratio', 'N/A')}
Benchmark Index: {fund_data.get('benchmark', 'N/A')}
AUM: {fund_data.get('aum', 'N/A')}
Inception Date: {fund_data.get('inception_date', 'N/A')}
Minimum Investment: Lumpsum/SIP - {fund_data.get('min_lumpsum_sip', 'N/A')}
Exit Load: {fund_data.get('exit_load', 'N/A')}
Lock-in Period: {fund_data.get('lock_in', 'N/A')}
Portfolio Turnover: {fund_data.get('turnover', 'N/A')}
Risk Level: {fund_data.get('risk', 'N/A')}
SEBI Riskometer: {fund_data.get('riskometer_category', 'N/A')}
Fund Managers: {fund_data.get('fund_managers', 'N/A')}
ELSS Fund: {fund_data.get('is_elss', 'N/A')}
Scheme Code (AMFI): {fund_data.get('scheme_code', 'N/A')}
ISIN: {fund_data.get('isin_growth', 'N/A')}
    """.strip()
    
    chunks.append(Document(
        page_content=summary_content,
        metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "summary", "source": fund_slug}
    ))
    
    # ---- 2. INDIVIDUAL KEY FIELD CHUNKS ----
    key_fields = {
        "expense_ratio": f"The Expense Ratio of {fund_name} is {fund_data.get('expense_ratio', 'N/A')}.",
        "exit_load": f"The Exit Load for {fund_name} is {fund_data.get('exit_load', 'N/A')}.",
        "min_sip": f"The Minimum SIP for {fund_name} is {fund_data.get('min_sip_amount', fund_data.get('min_lumpsum_sip', 'N/A'))}. Minimum Lumpsum is {fund_data.get('min_lumpsum_amount', 'N/A')}.",
        "lock_in": f"The Lock-in period for {fund_name} is {fund_data.get('lock_in', 'N/A')}.",
        "benchmark": f"The benchmark index for {fund_name} is {fund_data.get('benchmark', 'N/A')} ({fund_data.get('benchmark_index_variant', 'TRI')}).",
        "risk": f"The risk level (riskometer) for {fund_name} is {fund_data.get('riskometer_category', fund_data.get('risk', 'N/A'))}.",
        "aum": f"The Assets Under Management (AUM) of {fund_name} is {fund_data.get('aum', 'N/A')}.",
        "nav": f"The latest NAV of {fund_name} is {fund_data.get('nav', 'N/A')} as of {fund_data.get('nav_date', 'N/A')}. 52-week high: {fund_data.get('nav_52w_high', 'N/A')}, 52-week low: {fund_data.get('nav_52w_low', 'N/A')}.",
        "inception": f"{fund_name} was launched on {fund_data.get('inception_date', 'N/A')}. Since inception CAGR return is {fund_data.get('inception_return', 'N/A')}%.",
    }
    
    for field, content in key_fields.items():
        chunks.append(Document(
            page_content=content,
            metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": field, "source": fund_slug}
        ))
    
    # ---- 3. RETURNS WITH BENCHMARK COMPARISON ----
    returns_text = f"""Returns comparison for {fund_name}:
1 Month: Fund {fund_data.get('return_1m', 'N/A')}, Benchmark {fund_data.get('return_1m_benchmark', 'N/A')}, Category Avg {fund_data.get('return_1m_category_avg', 'N/A')}
3 Months: Fund {fund_data.get('return_3m', 'N/A')}, Benchmark {fund_data.get('return_3m_benchmark', 'N/A')}, Category Avg {fund_data.get('return_3m_category_avg', 'N/A')}
6 Months: Fund {fund_data.get('return_6m', 'N/A')}, Benchmark {fund_data.get('return_6m_benchmark', 'N/A')}, Category Avg {fund_data.get('return_6m_category_avg', 'N/A')}
1 Year: Fund {fund_data.get('return_1y', 'N/A')}, Benchmark {fund_data.get('return_1y_benchmark', 'N/A')}, Category Avg {fund_data.get('return_1y_category_avg', 'N/A')}, Rank {fund_data.get('return_1y_category_rank', 'N/A')}
3 Years: Fund {fund_data.get('return_3y', 'N/A')}, Benchmark {fund_data.get('return_3y_benchmark', 'N/A')}, Category Avg {fund_data.get('return_3y_category_avg', 'N/A')}, Rank {fund_data.get('return_3y_category_rank', 'N/A')}
5 Years: Fund {fund_data.get('return_5y', 'N/A')}, Benchmark {fund_data.get('return_5y_benchmark', 'N/A')}, Category Avg {fund_data.get('return_5y_category_avg', 'N/A')}
{fund_data.get('performance_highlight', '')}"""
    
    chunks.append(Document(
        page_content=returns_text.strip(),
        metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "returns_comparison", "source": fund_slug}
    ))
    
    # ---- 4. RISK METRICS ----
    risk_text = f"""Risk metrics for {fund_name} (3-year):
Alpha: {fund_data.get('alpha_3y', 'N/A')}
Beta: {fund_data.get('beta_3y', 'N/A')}
Sharpe Ratio: {fund_data.get('sharpe_3y', 'N/A')}
Sortino Ratio: {fund_data.get('sortino_3y', 'N/A')}
Information Ratio: {fund_data.get('info_ratio_3y', 'N/A')}
Standard Deviation: {fund_data.get('standard_deviation', 'N/A')}
Portfolio Turnover: {fund_data.get('turnover', 'N/A')}"""
    
    chunks.append(Document(
        page_content=risk_text.strip(),
        metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "risk_metrics", "source": fund_slug}
    ))
    
    # ---- 5. HOLDINGS CHUNK ----
    top_holdings = fund_data.get("top_holdings", [])
    if top_holdings:
        holdings_lines = [f"Top holdings of {fund_name} ({fund_data.get('total_holdings_count', 'N/A')} total):"]
        for i, h in enumerate(top_holdings[:10], 1):
            line = f"{i}. {h.get('name', 'N/A')} - {h.get('allocation_pct', 'N/A')} allocation, Sector: {h.get('sector', 'N/A')}"
            change = h.get('change_pct', '')
            if change and change != '0%':
                line += f", Change: {change}"
            holdings_lines.append(line)
        
        chunks.append(Document(
            page_content="\n".join(holdings_lines),
            metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "holdings", "source": fund_slug}
        ))
    
    # ---- 6. SECTOR ALLOCATION CHUNK ----
    sector_alloc = fund_data.get("sector_allocation", [])
    if sector_alloc:
        equity_sectors = [s for s in sector_alloc if s.get("asset_class", "").lower() == "equity"]
        if equity_sectors:
            sector_lines = [f"Sector allocation of {fund_name} (Equity portion):"]
            for s in equity_sectors:
                sector_lines.append(f"- {s.get('name', 'N/A')}: {s.get('pct', 'N/A')}")
            chunks.append(Document(
                page_content="\n".join(sector_lines),
                metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "sector_allocation", "source": fund_slug}
            ))
    
    # ---- 7. ASSET ALLOCATION CHUNK ----
    asset_alloc = fund_data.get("asset_allocation", [])
    if asset_alloc:
        alloc_lines = [f"Asset allocation of {fund_name}:"]
        for a in asset_alloc:
            line = f"- {a.get('name', 'N/A')}: {a.get('pct', 'N/A')}"
            breakdown = a.get("breakdown", [])
            if breakdown:
                parts = [f"{b.get('name', '')}: {b.get('pct', '')}" for b in breakdown]
                line += f" (Breakdown: {', '.join(parts)})"
            alloc_lines.append(line)
        
        # Market cap
        mca = fund_data.get("market_cap_allocation", {})
        if mca:
            alloc_lines.append(f"Market Cap Allocation: Large Cap {mca.get('large_cap_pct', 'N/A')}, Mid Cap {mca.get('mid_cap_pct', 'N/A')}, Small Cap {mca.get('small_cap_pct', 'N/A')}")
        
        chunks.append(Document(
            page_content="\n".join(alloc_lines),
            metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "asset_allocation", "source": fund_slug}
        ))
    
    # ---- 8. TAX & COSTS CHUNK ----
    tax = fund_data.get("taxation", {})
    if tax:
        tax_text = f"""Taxation and costs for {fund_name}:
Tax Category: {tax.get('fund_tax_category', 'N/A')}
STCG Tax: {tax.get('stcg_tax_rate', 'N/A')} (holding period: {tax.get('stcg_holding_period', 'N/A')})
LTCG Tax: {tax.get('ltcg_tax_rate', 'N/A')} (holding period: {tax.get('ltcg_holding_period', 'N/A')})
LTCG Exemption: {tax.get('ltcg_exemption_limit', 'N/A')}
Indexation Benefit: {tax.get('indexation_benefit', 'N/A')}
Section 80C Eligible: {tax.get('section_80c_eligible', 'N/A')}
STT Applicable: {tax.get('stt_applicable', 'N/A')}
Stamp Duty: {tax.get('stamp_duty', 'N/A')}
Expense Ratio (Direct): {fund_data.get('expense_ratio', 'N/A')}
Dividend Tax: {tax.get('dividend_tax_treatment', 'N/A')}"""
        
        chunks.append(Document(
            page_content=tax_text.strip(),
            metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "taxation", "source": fund_slug}
        ))
    
    # ---- 9. SIP MECHANICS CHUNK ----
    sip = fund_data.get("sip_mechanics", {})
    if sip:
        sip_text = f"""SIP details for {fund_name}:
SIP Available: {sip.get('sip_available', 'N/A')}
SIP Frequencies: {', '.join(sip.get('sip_frequencies', [])) or 'N/A'}
SIP Dates: {', '.join(str(d) for d in sip.get('sip_dates', [])) or 'N/A'}
Minimum SIP Amount: {sip.get('sip_min_amount', fund_data.get('min_sip_amount', 'N/A'))}
Minimum SIP Installments: {sip.get('sip_min_installments', 'N/A')}
SIP Pause Facility: {sip.get('sip_pause_facility', 'N/A')}
SIP Step-up Facility: {sip.get('sip_step_up_facility', 'N/A')}
Perpetual SIP: {sip.get('perpetual_sip', 'N/A')}"""
        
        chunks.append(Document(
            page_content=sip_text.strip(),
            metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "sip_mechanics", "source": fund_slug}
        ))
    
    # ---- 10. REDEMPTION CHUNK ----
    redemption = fund_data.get("redemption_details", {})
    if redemption:
        exit_struct = redemption.get("exit_load_structure", {})
        redemption_text = f"""Redemption details for {fund_name}:
Lock-in Period: {redemption.get('lock_in_period', 'N/A')}
Partial Redemption: {redemption.get('partial_redemption_allowed', 'N/A')}
Redemption Processing: {redemption.get('redemption_processing_time', 'N/A')}
NAV Cut-off (Purchase): {redemption.get('cutoff_time_purchase', 'N/A')}
NAV Cut-off (Redemption): {redemption.get('cutoff_time_redemption', 'N/A')}
Settlement: {redemption.get('settlement_type', 'N/A')}
Exit Load: {exit_struct.get('pct', 'N/A')} ({exit_struct.get('window', 'N/A')})
Exit Load Nil Beyond: {exit_struct.get('nil_beyond', 'N/A')}
Units Pledgeable: {redemption.get('units_pledgeable', 'N/A')}"""
        
        chunks.append(Document(
            page_content=redemption_text.strip(),
            metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "redemption", "source": fund_slug}
        ))
    
    # ---- 11. FUND MANAGER CHUNK ----
    managers = fund_data.get("fund_managers_detail", [])
    if managers:
        mgr_lines = [f"Fund managers of {fund_name}:"]
        for m in managers:
            mgr_lines.append(f"- {m.get('name', 'N/A')}: {m.get('subtitle', 'N/A')}")
        
        chunks.append(Document(
            page_content="\n".join(mgr_lines),
            metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "fund_managers", "source": fund_slug}
        ))
    
    # ---- 12. RANKING CHUNK ----
    ranking_info = fund_data.get("ranking_info", "")
    ranking_scores = fund_data.get("ranking_scores", {})
    ranking_pros = fund_data.get("ranking_pros", [])
    ranking_cons = fund_data.get("ranking_cons", [])
    if ranking_info or ranking_scores:
        rank_text = f"INDmoney Ranking for {fund_name}:\n{ranking_info}"
        if ranking_scores:
            rank_text += "\nScores: " + ", ".join(f"{k}: {v}" for k, v in ranking_scores.items())
        if ranking_pros:
            rank_text += "\nPros: " + "; ".join(ranking_pros)
        if ranking_cons:
            rank_text += "\nCons: " + "; ".join(ranking_cons)
        
        chunks.append(Document(
            page_content=rank_text.strip(),
            metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "ranking", "source": fund_slug}
        ))
    
    # ---- 13. ABOUT SECTION CHUNKS (SPLIT) ----
    about_text = fund_data.get('about', '')
    if about_text:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=60,
            separators=["\n\n", "\n", ". ", " "]
        )
        about_chunks = text_splitter.split_text(about_text)
        for i, text in enumerate(about_chunks):
            chunks.append(Document(
                page_content=f"About {fund_name}: {text}",
                metadata={"fund_name": fund_name, "fund_slug": fund_slug, "field_type": "about", "chunk_index": i, "source": fund_slug}
            ))
            
    return chunks


def process_and_store(clear_collection=False):
    # 1. Initialize Embeddings
    print(f"Initializing embedding model: {EMBEDDING_MODEL}...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    
    # 2. Load Processed JSONs
    all_chunks = []
    for json_file in PROCESSED_DATA_DIR.glob("*.json"):
        print(f"Loading {json_file.name}...")
        with open(json_file, "r", encoding="utf-8") as f:
            fund_data = json.load(f)
            chunks = create_fund_chunks(fund_data, fund_slug_param=json_file.stem)
            all_chunks.extend(chunks)
    
    if not all_chunks:
        print("No chunks generated. Skipping vector storage.")
        return

    # 3. Store in ChromaDB
    print(f"Storing {len(all_chunks)} chunks in ChromaDB at {VECTORSTORE_DIR}...")
    
    # Ensure directory exists
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    
    if clear_collection:
        print("Clearing existing collection 'indmoney_mf_rag' for fresh ingest...")
        # Load and delete all
        db = Chroma(
            persist_directory=str(VECTORSTORE_DIR),
            embedding_function=embeddings,
            collection_name="indmoney_mf_rag"
        )
        # Get all IDs and delete
        existing_data = db.get()
        if existing_data["ids"]:
            db.delete(ids=existing_data["ids"])
            print(f"Deleted {len(existing_data['ids'])} existing documents.")

    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=str(VECTORSTORE_DIR),
        collection_name="indmoney_mf_rag"
    )
    
    print("Vector store updated successfully!")

if __name__ == "__main__":
    process_and_store()
