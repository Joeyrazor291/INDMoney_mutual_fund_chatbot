import os
import re
from typing import List

class SafetyGuardrails:
    @staticmethod
    def contains_pii(text: str) -> bool:
        """
        Checks if the text contains potential PII like PAN, Aadhaar, Phone, Email.
        """
        patterns = {
            "PAN": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
            "Aadhaar": r"\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b",
            "Phone": r"\b(?:\+91|91)?[6-9]\d{9}\b",
            "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        }
        
        for name, pattern in patterns.items():
            if re.search(pattern, text):
                return True
        return False

    @staticmethod
    def is_opinionated(query: str) -> bool:
        """
        Checks if the query is seeking investment advice or opinions.
        """
        advice_keywords = [
            "should i buy", "should i sell", "is it good", "best fund", 
            "recommend", "suggest", "worth investing", "buy or sell",
            "which one is better", "top pick"
        ]
        query_lower = query.lower()
        return any(kw in query_lower for kw in advice_keywords)

    @staticmethod
    def is_performance_comparison(query: str) -> bool:
        """
        Checks if the user is asking to compare or compute returns.
        """
        comp_keywords = ["better returns", "highest return", "calculate profit", "which fund is better"]
        query_lower = query.lower()
        return any(kw in query_lower for kw in comp_keywords)

    @staticmethod
    def get_refusal_message() -> str:
        return ("I can only provide factual data about these mutual funds. "
                "For investment advice or portfolio recommendations, please consult a SEBI-registered advisor. "
                "You can learn more about picking funds here: https://www.indmoney.com/mutual-funds/guide")

    @staticmethod
    def get_pii_block_message() -> str:
        return "I'm sorry, but I cannot process requests containing personal information like PAN, Aadhaar, or contact details for security reasons."
