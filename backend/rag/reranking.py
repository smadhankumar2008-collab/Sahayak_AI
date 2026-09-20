"""
Simple reranking for Sahayak AI
"""
from typing import List, Dict
import re

def rerank_documents(query: str, documents: List[Dict]) -> List[Dict]:
    """
    Rerank retrieved documents based on additional signals
    """
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    
    for doc in documents:
        chunk = doc.get("chunk", "").lower()
        title = doc.get("title", "").lower()
        
        # Exact phrase bonus
        phrase_bonus = 0
        if query_lower in chunk:
            phrase_bonus += 0.5
        if query_lower in title:
            phrase_bonus += 0.8
        
        # Question type specific boosting
        if "document" in query_lower and "document" in chunk:
            phrase_bonus += 0.2
        if "eligible" in query_lower and "eligible" in chunk:
            phrase_bonus += 0.2
        if "how to" in query_lower and ("how to" in chunk or "procedure" in chunk or "apply" in chunk):
            phrase_bonus += 0.2
        
        doc["retrieval_score"] = doc.get("retrieval_score", 0) + phrase_bonus
    
    # Re-sort
    documents.sort(key=lambda x: x.get("retrieval_score", 0), reverse=True)
    return documents
