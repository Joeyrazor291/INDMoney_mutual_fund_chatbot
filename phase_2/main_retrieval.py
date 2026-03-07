from phase_2.query_processor import process_query
from phase_2.retriever import INDMoneyRetriever

def run_rag_retrieval(user_query: str):
    print(f"\n{'='*50}")
    print(f"USER QUERY: {user_query}")
    print(f"{'='*50}")
    
    # 1. Process Query (Resolution & Intent)
    processed = process_query(user_query)
    fund_slug = processed["resolved_fund"]
    intents = processed["intents"]
    
    print(f"-> Resolved Fund: {fund_slug}")
    print(f"-> Detected Intents: {intents}")
    
    # 2. Retrieve Context Chunks
    # Use the first intent if multiple are detected for filtering, otherwise any
    primary_intent = intents[0] if intents else None
    
    retriever = INDMoneyRetriever()
    docs = retriever.retrieve(user_query, fund_slug=fund_slug, intent=primary_intent)
    
    print(f"\nRETRIEVED CONTEXT ({len(docs)} chunks):")
    for i, doc in enumerate(docs):
        fund_name = doc.metadata.get("fund_name", "Unknown")
        field_type = doc.metadata.get("field_type", "general")
        print(f"\n[{i+1}] Source: {fund_name} | Field: {field_type}")
        print(f"    Content: {doc.page_content[:200]}...")
    
    return docs

if __name__ == "__main__":
    # Sample questions to test the pipeline
    samples = [
        "What is the expense ratio of HDFC Mid Cap?",
        "Tell me about the exit load for ABSL Quant",
        "Minimum investment for Edelweiss index fund",
        "Who is the manager of HDFC Flexicap?",
        "How is the performance of Aditya Birla Sun Life ELSS Tax Saver?"
    ]
    
    for sample in samples:
        run_rag_retrieval(sample)
