from phase_2.query_processor import process_query
from phase_2.retriever import INDMoneyRetriever
from phase_3.llm_engine import GroqLLMEngine
from phase_3.guardrails import SafetyGuardrails

class INDMoneyChatbot:
    def __init__(self):
        self.retriever = INDMoneyRetriever()
        self.llm_engine = GroqLLMEngine()
        self.guardrails = SafetyGuardrails()

    def ask(self, query: str):
        print(f"\nUser Query: {query}")
        
        # 1. PII Check
        if self.guardrails.contains_pii(query):
            print("Guardrail: PII Detected")
            return self.guardrails.get_pii_block_message()
            
        # 2. Advice/Opinion Check
        if self.guardrails.is_opinionated(query) or self.guardrails.is_performance_comparison(query):
            print("Guardrail: Opinion/Performance claim detected")
            return self.guardrails.get_refusal_message()

        # 3. Process Query (Fund resolution)
        processed = process_query(query)
        fund_slug = processed["resolved_fund"]
        intents = processed["intents"]
        
        # 4. Retrieval
        primary_intent = intents[0] if intents else None
        print(f"Retrieving context for fund: {fund_slug}, intent: {primary_intent}...")
        context_docs = self.retriever.retrieve(query, fund_slug=fund_slug, intent=primary_intent)
        
        if not context_docs:
            return "I don't have that information. Please check indmoney.com for the latest details."

        # 5. Generation
        print("Generating answer via Groq...")
        answer = self.llm_engine.generate_answer(query, context_docs)
        
        return answer

if __name__ == "__main__":
    chatbot = INDMoneyChatbot()
    
    # Test queries
    test_queries = [
        "What is the expense ratio of HDFC Mid Cap?",
        "Should I buy ABSL Quant Fund?",
        "My PAN is ABCDE1234F, tell me my returns.",
        "What is the exit load for Edelweiss Nifty Next 50?",
        "Who manages HDFC Flexicap?",
        "Which fund is best for me?"
    ]
    
    for q in test_queries:
        print("-" * 30)
        response = chatbot.ask(q)
        print(f"Chatbot: {response}")
