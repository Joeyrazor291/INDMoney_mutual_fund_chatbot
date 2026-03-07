import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

SYSTEM_PROMPT = """You are an expert mutual fund assistant for INDMoney.
Your ONLY job is to answer factual questions about the 5 specific mutual funds provided in the context.

STRICT RULES:
1. Answer ONLY using the provided CONTEXT. If the information is not present, say: "I don't have that information. Please check indmoney.com."
2. Never provide investment advice or opinions (Buy/Sell/Hold). If asked, decline politely.
3. Do not compute or compare returns.
4. Maximum 3 sentences per answer.
5. Include exactly ONE citation link from the metadata provided in the context. You MUST use the exact URL provided in 'IMPORTANT_CITATION_TO_USE' at the end of the context.
6. The citation should be formatted as a Markdown link, e.g., [Source](URL).
7. End every answer with: "\n\nLast updated from sources"
8. Do NOT process or repeat any PII (PAN, Aadhaar, etc.) if mentioned in user query.

CONTEXT:
{context}
"""

# Fund Slug to URL Mapping
FUND_CITATIONS = {
    "hdfc-mid-cap": "https://www.indmoney.com/mutual-funds/hdfc-mid-cap-fund-direct-plan-growth-option-3097",
    "hdfc-flexi-cap": "https://www.indmoney.com/mutual-funds/hdfc-flexi-cap-fund-direct-plan-growth-option-3184",
    "absl-quant": "https://www.indmoney.com/mutual-funds/aditya-birla-sun-life-quant-fund-direct-growth-1046035",
    "absl-elss": "https://www.indmoney.com/mutual-funds/aditya-birla-sun-life-elss-tax-saver-direct-plan-growth-21308",
    "edelweiss-nifty-next-50": "https://www.indmoney.com/mutual-funds/edelweiss-nifty-next-50-index-fund-direct-growth-1042502"
}

class GroqLLMEngine:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment.")
            
        self.llm = ChatGroq(
            model=model_name,
            temperature=0,
            max_tokens=512,
            api_key=api_key
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{query}")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_answer(self, query: str, context_docs: list):
        # Format context and extract a unique citation link
        context_text = ""
        citation_link = "https://www.indmoney.com" # Fallback
        
        # We'll take the citation from the first document that has a valid known slug
        # as the first document is usually the most relevant.
        for doc in context_docs:
            context_text += f"\n--- CHUNK ---\n{doc.page_content}\n"
            slug = doc.metadata.get("fund_slug")
            if citation_link == "https://www.indmoney.com" and slug in FUND_CITATIONS:
                citation_link = FUND_CITATIONS[slug]

        # If we have a citation link, append it to the context so LLM can use it
        formatted_context = f"{context_text}\n\nIMPORTANT_CITATION_TO_USE: {citation_link}"
        
        response = self.chain.invoke({
            "query": query,
            "context": formatted_context
        })
        
        # Post-process to ensure the footer is correctly formatted (sometimes LLMs add extra newlines)
        response = response.strip()
        if "Last updated from sources" not in response:
            response += "\n\nLast updated from sources"
            
        return response

if __name__ == "__main__":
    # Internal test
    engine = GroqLLMEngine()
    print("Groq Engine Initialized.")
