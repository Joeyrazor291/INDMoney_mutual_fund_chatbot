import re
from rapidfuzz import process, fuzz

# Canonical fund list from Phase 1
FUND_MAPPING = {
    "hdfc-mid-cap": ["HDFC Mid Cap Fund", "HDFC Mid Cap Opportunities", "HDFC Midcap"],
    "hdfc-flexi-cap": ["HDFC Flexi Cap Fund", "HDFC Flexicap"],
    "absl-quant": ["Aditya Birla Sun Life Quant Fund", "ABSL Quant", "Aditya Birla Quant"],
    "absl-elss": ["Aditya Birla Sun Life ELSS Tax Saver Fund", "ABSL ELSS", "Aditya Birla Tax Saver"],
    "edelweiss-nifty-next-50": ["Edelweiss Nifty Next 50 Index Fund", "Edelweiss Nifty Next 50", "Edelweiss Index Fund"]
}

# Intent mapping keywords
INTENT_KEYWORDS = {
    "expense_ratio": ["expense ratio", "fees", "charges", "cost", "ter"],
    "exit_load": ["exit load", "redemption fee", "withdrawal charges"],
    "sip_mechanics": ["minimum sip", "min sip", "min lumpsum", "starting amount", "minimum investment"],
    "lock_in": ["lock in", "lockin", "lock period", "holding period"],
    "returns_comparison": ["benchmark", "index", "target index", "returns", "performance", "yield", "1 year return", "3 year return", "profit"],
    "risk_metrics": ["risk", "riskometer", "how risky", "volatility", "alpha", "beta", "sharpe", "sortino"],
    "fund_managers": ["manager", "fund manager", "managed by"],
    "capital_gains": ["capital gains", "tax statement", "download statement", "tax report"]
}

def resolve_fund(query: str, threshold: int = 70):
    """
    Resolves the fund name mentioned in the query to a canonical slug.
    """
    # Remove the front-end 'Focus funds' context for accurate matching of the user's specific request
    clean_query = re.sub(r'\(Focus funds:.*?\)', '', query).strip()
    
    best_match = None
    highest_score = 0
    
    for slug, aliases in FUND_MAPPING.items():
        # Check against each alias
        match = process.extractOne(clean_query, aliases, scorer=fuzz.partial_ratio)
        if match and match[1] > highest_score:
            highest_score = match[1]
            best_match = slug
            
    if highest_score >= threshold:
        return best_match
    return None

def detect_intent(query: str):
    """
    Detects the user intent/field interest based on keywords.
    """
    query_lower = query.lower()
    detected_intents = []
    
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            detected_intents.append(intent)
            
    return detected_intents

def process_query(query: str):
    """
    Combines fund resolution and intent detection.
    """
    return {
        "original_query": query,
        "resolved_fund": resolve_fund(query),
        "intents": detect_intent(query)
    }

if __name__ == "__main__":
    # Test cases
    test_queries = [
        "What is the expense ratio of HDFC Mid Cap?",
        "Tell me about the exit load for ABSL Quant",
        "Minimum investment for Edelweiss index fund",
        "How to download tax statement?",
        "Who is the manager of HDFC Flexicap?"
    ]
    
    for q in test_queries:
        print(f"\nQuery: {q}")
        print(f"Result: {process_query(q)}")
