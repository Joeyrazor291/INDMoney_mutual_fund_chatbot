import os
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = BASE_DIR / "data" / "vectorstore"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

def debug_vstore():
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
    
    data = vectorstore.get()
    print(f"Keys in get(): {data.keys()}")
    print(f"Number of documents: {len(data['documents'])}")
    if len(data['documents']) > 0:
        print(f"First document snippet: {data['documents'][0][:100]}")
    else:
        print("Vector store is EMPTY for this collection.")

if __name__ == "__main__":
    debug_vstore()
