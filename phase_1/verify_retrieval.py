import os
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = BASE_DIR / "data" / "vectorstore"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

def verify():
    print(f"Loading embeddings: {EMBEDDING_MODEL}...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    
    print(f"Loading vector store from {VECTORSTORE_DIR}...")
    vectorstore = Chroma(
        persist_directory=str(VECTORSTORE_DIR),
        embedding_function=embeddings,
        collection_name="indmoney_mf_rag"
    )
    
    test_queries = [
        "What is the expense ratio of HDFC Mid Cap Fund?",
        "Exit load for ABSL Quant Fund",
        "Minimum SIP for Edelweiss Nifty Next 50",
        "Risk level of HDFC Flexi Cap",
        "How to download capital gains statement?"
    ]
    
    for query in test_queries:
        print(f"\nQUERY: {query}")
        results = vectorstore.similarity_search(query, k=3)
        print(f"Found {len(results)} results:")
        for doc in results:
            print(f"- [Fund: {doc.metadata.get('fund_name')}, Type: {doc.metadata.get('field_type')}]")
            print(f"  Content snippet: {doc.page_content[:150]}...")

if __name__ == "__main__":
    verify()
