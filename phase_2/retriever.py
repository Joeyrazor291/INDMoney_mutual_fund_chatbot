import os
from pathlib import Path
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
try:
    from langchain.retrievers import EnsembleRetriever
except ImportError:
    from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = BASE_DIR / "data" / "vectorstore"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

class INDMoneyRetriever:
    def __init__(self, collection_name: str = "indmoney_mf_rag"):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        
        # Load Chroma Vector Store
        print(f"DEBUG: Vectorstore path: {VECTORSTORE_DIR}")
        self.vectorstore = Chroma(
            persist_directory=str(VECTORSTORE_DIR),
            embedding_function=self.embeddings,
            collection_name=collection_name
        )
        
        # Initialize BM25 and Hybrid Retriever
        data = self.vectorstore.get()
        self.all_docs = data["documents"]
        self.all_metadatas = data["metadatas"]
        
        print(f"DEBUG: Loaded {len(self.all_docs)} documents from vectorstore.")

        if not self.all_docs:
            raise ValueError(f"No documents found in Chroma collection '{collection_name}'. "
                             f"Please run phase_1/main_ingestion.py first.")
        
        # Convert to Document objects for BM25
        self.documents = [
            Document(page_content=text, metadata=meta) 
            for text, meta in zip(self.all_docs, self.all_metadatas)
        ]
        
        self.bm25_retriever = BM25Retriever.from_documents(self.documents)
        self.bm25_retriever.k = 5
        self.dense_retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        
        # Ensemble Retriever (Hybrid)
        self.hybrid_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, self.dense_retriever],
            weights=[0.4, 0.6]
        )

    def retrieve(self, query: str, fund_slug: str = None, intent: str = None):
        """
        Retrieves context chunks with optional metadata filtering.
        """
        # Apply metadata filtering if specified
        filters = {}
        if fund_slug:
            filters["fund_slug"] = fund_slug
        if intent and intent in ["expense_ratio", "exit_load", "sip_mechanics", "lock_in", "returns_comparison", "risk_metrics", "fund_managers"]:
            filters["field_type"] = intent
            
        print(f"DEBUG: Applying filters: {filters}")
        
        if filters:
            # Construct Chroma-style 'where' filter
            if len(filters) > 1:
                where_filter = {"$and": [{k: {"$eq": v}} for k, v in filters.items()]}
            else:
                k, v = list(filters.items())[0]
                where_filter = {k: {"$eq": v}}
            
            # Use direct similarity search with explicit 'where' filter
            results = self.vectorstore.similarity_search(
                query, 
                k=5, 
                filter=where_filter
            )
            
            # If no filtered results are found, fall back to hybrid search (unfiltered)
            if len(results) == 0:
                print("DEBUG: 0 filtered results, falling back to hybrid.")
                results = self.hybrid_retriever.invoke(query)
        else:
            results = self.hybrid_retriever.invoke(query)
            
        return self._deduplicate(results)

    def _deduplicate(self, docs: List[Document]):
        """
        Deduplicates results based on page content.
        """
        seen_content = set()
        unique_docs = []
        for doc in docs:
            if doc.page_content not in seen_content:
                unique_docs.append(doc)
                seen_content.add(doc.page_content)
        return unique_docs
