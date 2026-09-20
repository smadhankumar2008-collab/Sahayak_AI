"""
Hybrid Retrieval for Sahayak AI - FIXED for relevance filtering
Implements:
- Topic filtering (COOPERATIVE_LAW, PACS_SERVICE, etc.)
- Relevance threshold
- Deduplication
- No mixing of unrelated chunks
"""
import json
import os
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import re
import hashlib

from .embeddings import EmbeddingModel
from ..chatbot.language import classify_query_domain

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# Topic mapping for filtering
TOPIC_KEYWORDS = {
    "COOPERATIVE_LAW": ["act", "section", "law", "bye-law", "rights", "election", "board", "audit", "member rights", "உரிமை", "अधिकार", "അവകാശ"],
    "PACS_SERVICE": ["pacs", "membership", "loan", "deposit", "kcc", "services", "சேர", "दस्तावेज", "சேவை"],
    "CROP_INSURANCE": ["pmfby", "crop insurance", "insurance", "bima", "claim", "premium", "பயிர்", "फसल"],
    "GRIEVANCE_REDDRESSAL": ["grievance", "complaint", "cpgrams", "pgportal", "புகார்", "शिकायत", "പരാതി"],
    "GOVERNMENT_SCHEME": ["scheme", "yojana", "policy", "computerization", "storage", "csc", "myscheme", "திட்டம்"],
    "FINANCIAL_LITERACY": ["financial", "savings", "interest", "banking", "literacy"],
    "COOPERATIVE_GOVERNANCE": ["governance", "board", "committee", "meeting"],
}

# Irrelevant content that should NOT be mixed
IRRELEVANT_PATTERNS = [
    "sahakar mitra internship",
    "internship programme",
    "sip scheme",
]

class HybridRetriever:
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or DATA_DIR
        self.documents: List[Dict] = []
        self.embeddings: Optional[np.ndarray] = None
        self.embedding_model: Optional[EmbeddingModel] = None
        self.faiss_index = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.use_faiss = False
        self.use_transformer = False
        self._load()
    
    def _load(self):
        print(f"Loading retriever from {self.data_dir}")
        metadata_path = self.data_dir / "metadata.json"
        if not metadata_path.exists():
            print(f"Metadata not found at {metadata_path}")
            return
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)
        print(f"Loaded {len(self.documents)} documents")
        
        # Deduplicate documents by content hash
        seen_hashes = set()
        deduped = []
        for doc in self.documents:
            chunk = doc.get("chunk", "")
            h = hashlib.md5(chunk.encode('utf-8')).hexdigest()
            if h not in seen_hashes:
                seen_hashes.add(h)
                deduped.append(doc)
        if len(deduped) < len(self.documents):
            print(f"Deduplicated: {len(self.documents)} -> {len(deduped)}")
            self.documents = deduped
        
        info_path = self.data_dir / "ingestion_info.json"
        model_name = None
        if info_path.exists():
            try:
                with open(info_path, 'r') as f:
                    info = json.load(f)
                    model_name = info.get("model_name")
                    self.use_transformer = info.get("use_transformer", False)
            except:
                pass
        
        self.embedding_model = EmbeddingModel(model_name=model_name)
        tfidf_path = self.data_dir / "tfidf_vectorizer.pkl"
        if tfidf_path.exists():
            try:
                with open(tfidf_path, 'rb') as f:
                    self.embedding_model.tfidf_vectorizer = pickle.load(f)
                print("Loaded TF-IDF vectorizer")
                texts = [doc["chunk"] for doc in self.documents]
                self.tfidf_matrix = self.embedding_model.tfidf_vectorizer.transform(texts)
            except Exception as e:
                print(f"Failed to load TF-IDF: {e}")
        
        faiss_path = self.data_dir / "vector_store.faiss"
        npy_path = self.data_dir / "vector_store.npy"
        if faiss_path.exists():
            try:
                import faiss
                self.faiss_index = faiss.read_index(str(faiss_path))
                self.use_faiss = True
                print(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors")
            except Exception as e:
                print(f"FAISS load failed: {e}")
                self.use_faiss = False
        
        if not self.use_faiss and npy_path.exists():
            try:
                self.embeddings = np.load(str(npy_path))
                print(f"Loaded numpy embeddings: {self.embeddings.shape}")
            except Exception as e:
                print(f"Numpy load failed: {e}")
        
        if self.embeddings is None and not self.use_faiss:
            if self.tfidf_matrix is not None:
                self.embeddings = self.tfidf_matrix.toarray()
                norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1
                self.embeddings = self.embeddings / norms
                print(f"Using TF-IDF embeddings: {self.embeddings.shape}")
    
    def _semantic_search(self, query_embedding: np.ndarray, top_k: int = 20) -> List[Tuple[int, float]]:
        if self.use_faiss and self.faiss_index is not None:
            try:
                import faiss
                query_vec = query_embedding.reshape(1, -1).astype('float32')
                faiss.normalize_L2(query_vec)
                scores, indices = self.faiss_index.search(query_vec, top_k)
                results = []
                for idx, score in zip(indices[0], scores[0]):
                    if idx != -1:
                        results.append((int(idx), float(score)))
                return results
            except Exception as e:
                print(f"FAISS search failed: {e}")
        if self.embeddings is not None:
            query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
            scores = np.dot(self.embeddings, query_norm)
            top_indices = np.argsort(scores)[::-1][:top_k]
            results = [(int(i), float(scores[i])) for i in top_indices]
            return results
        return []
    
    def _keyword_search(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        expanded_query = query
        synonyms = {
            "documents": "membership application form identity address proof",
            "join": "membership become apply",
            "required": "need eligibility",
            "pacs": "primary agricultural credit society",
            "pmfby": "pradhan mantri fasal bima yojana crop insurance",
            "grievance": "complaint cpgrams",
            "rights": "member rights act law",
            "உரிமை": "member rights act law cooperative",
            "services": "pacs services credit loan",
        }
        q_lower = query.lower()
        for key, syn in synonyms.items():
            if key in q_lower:
                expanded_query += " " + syn
        
        if self.tfidf_matrix is not None and self.embedding_model.tfidf_vectorizer is not None:
            try:
                query_vec = self.embedding_model.tfidf_vectorizer.transform([expanded_query])
                from sklearn.metrics.pairwise import cosine_similarity
                scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
                top_indices = np.argsort(scores)[::-1][:top_k]
                results = [(int(i), float(scores[i])) for i in top_indices if scores[i] > 0]
                return results
            except Exception as e:
                print(f"TF-IDF search failed: {e}")
        
        query_words = set(re.findall(r'\w+', query.lower()))
        results = []
        for idx, doc in enumerate(self.documents):
            chunk_lower = doc.get("chunk", "").lower()
            title_lower = doc.get("title", "").lower()
            chunk_words = set(re.findall(r'\w+', chunk_lower))
            title_words = set(re.findall(r'\w+', title_lower))
            overlap = len(query_words & chunk_words)
            title_overlap = len(query_words & title_words)
            score = (overlap / (len(query_words) + 1)) + (title_overlap * 0.5)
            for word in query_words:
                if len(word) > 3 and word in chunk_lower:
                    score += 0.1
            if score > 0:
                results.append((idx, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _authority_boost(self, doc: Dict) -> float:
        source_name = doc.get("source_name", "").lower()
        source_url = doc.get("source_url", "").lower()
        boost = 0.0
        if any(x in source_url or x in source_name for x in ["cooperation.gov.in", "gov.in", "nic.in", "pib.gov.in", "pmfby.gov.in"]):
            boost += 0.25
        if any(x in doc.get("chunk", "").lower() or x in doc.get("title", "").lower() for x in ["act", "section", "bye-law", "rule"]):
            boost += 0.15
        if any(x in source_name for x in ["nabard", "ncdc", "ncct"]):
            boost += 0.15
        last_verified = doc.get("metadata", {}).get("last_verified", "") if isinstance(doc.get("metadata"), dict) else ""
        if "2026" in str(last_verified) or "2025" in str(last_verified):
            boost += 0.05
        return boost
    
    def _is_relevant(self, doc: Dict, query: str, query_type: str) -> bool:
        """Check if document is relevant to query - prevent mixing unrelated chunks"""
        chunk_lower = doc.get("chunk", "").lower()
        title_lower = doc.get("title", "").lower()
        query_lower = query.lower()
        
        # Block irrelevant patterns
        for pattern in IRRELEVANT_PATTERNS:
            if pattern in chunk_lower and pattern not in query_lower:
                # If query is about PACS services but chunk is about internship, block it
                if "internship" in pattern and "internship" not in query_lower:
                    return False
        
        # For PACS services query, don't include internship schemes
        if query_type == "PACS_SERVICE":
            if "internship" in chunk_lower and "internship" not in query_lower:
                return False
            if "sahakar mitra" in chunk_lower and "mitra" not in query_lower and "internship" not in query_lower:
                return False
        
        # For member rights query, prioritize law documents
        if query_type == "COOPERATIVE_LAW":
            # If chunk is about KCC loan details but query is about rights, lower relevance
            if "kisan credit card" in chunk_lower and "rights" in query_lower and "credit" not in query_lower:
                # Check if it's really about rights
                if "right" not in chunk_lower and "act" not in chunk_lower and "law" not in chunk_lower:
                    return False
        
        # For PACS services, don't include pure KCC if query is general services
        if query_type == "PACS_SERVICE" and "services" in query_lower:
            if "kisan credit card" in title_lower and len(query_lower.split()) <= 6:
                # If query is "What are services provided by PACS", KCC alone is not sufficient, but can be included if relevant
                # Allow it but with lower priority - don't block, just let scoring handle
                pass
        
        return True
    
    def _topic_match_score(self, doc: Dict, query_type: str) -> float:
        """Boost score if doc topic matches query topic"""
        doc_type = doc.get("query_type", "") or doc.get("category", "")
        # Normalize
        mapping = {
            "LAW": "COOPERATIVE_LAW",
            "PACS": "PACS_SERVICE",
            "CROP_INSURANCE": "CROP_INSURANCE",
            "GRIEVANCE": "GRIEVANCE_REDDRESSAL",
            "SCHEME": "GOVERNMENT_SCHEME",
            "FINANCIAL_LITERACY": "FINANCIAL_LITERACY",
            "GENERAL_COOPERATIVE": "GENERAL_COOPERATIVE",
            "COOPERATIVE_LAW": "COOPERATIVE_LAW",
            "PACS_SERVICE": "PACS_SERVICE",
            "GOVERNMENT_SCHEME": "GOVERNMENT_SCHEME",
        }
        doc_type_norm = mapping.get(doc_type, doc_type)
        query_type_norm = mapping.get(query_type, query_type)
        
        if query_type_norm == doc_type_norm:
            return 0.3
        # Partial matches
        if query_type_norm == "PACS_SERVICE" and doc_type_norm == "GOVERNMENT_SCHEME":
            # Some schemes are PACS related, allow small boost
            return 0.05
        if query_type_norm == "COOPERATIVE_LAW" and doc_type_norm == "COOPERATIVE_GOVERNANCE":
            return 0.15
        return 0.0
    
    def retrieve(self, query: str, top_k: int = 6, query_type: str = None, threshold: float = 0.20) -> List[Dict]:
        if not self.documents:
            print("No documents loaded")
            return []
        if not query or not query.strip():
            return []
        
        if query_type is None:
            query_type = classify_query_domain(query)
        
        print(f"Retrieving for query: '{query[:50]}...' type: {query_type} threshold: {threshold}")
        
        if self.embedding_model is None:
            self.embedding_model = EmbeddingModel()
        if not self.embedding_model.use_transformer and self.embedding_model.tfidf_vectorizer is None:
            texts = [doc["chunk"] for doc in self.documents]
            self.embedding_model.fit_tfidf(texts)
        
        query_embedding = self.embedding_model.encode([query])[0]
        semantic_results = self._semantic_search(query_embedding, top_k=20)
        keyword_results = self._keyword_search(query, top_k=20)
        
        combined_scores = {}
        for idx, score in semantic_results:
            combined_scores[idx] = combined_scores.get(idx, 0) + score * 0.7
        for idx, score in keyword_results:
            combined_scores[idx] = combined_scores.get(idx, 0) + score * 0.3
        
        final_results = []
        for idx, base_score in combined_scores.items():
            if idx >= len(self.documents):
                continue
            doc = self.documents[idx]
            
            # Relevance check - prevent mixing unrelated
            if not self._is_relevant(doc, query, query_type):
                continue
            
            type_boost = self._topic_match_score(doc, query_type)
            authority_boost = self._authority_boost(doc)
            # Title exact match boost for upgraded DB - critical for EMI, savings etc.
            title_boost = 0.0
            title_lower = doc.get("title","").lower()
            query_lower = query.lower()
            # Exact title contains query or query contains title keywords
            if title_lower and len(title_lower) > 3:
                # If query is "What is EMI?" and title is "What is EMI" - strong boost
                if title_lower in query_lower or query_lower in title_lower:
                    title_boost += 0.4
                # For EMI, savings, etc - boost if title matches key term
                key_terms = ["emi", "savings", "current account", "interest", "secured", "unsecured", "repayment", "checklist", "rights", "documents", "responsibilities", "election", "managing committee", "violation", "pm-kisan", "crop insurance", "claim", "grievance", "complaint"]
                for term in key_terms:
                    if term in query_lower and term in title_lower:
                        title_boost += 0.2
                        break
            # Boost first chunk (chunk_index 0) which contains definition
            chunk_idx = doc.get("chunk_index", 0)
            if chunk_idx == 0:
                title_boost += 0.15
            
            final_score = base_score + type_boost + authority_boost + title_boost
            
            if final_score >= threshold:
                result_doc = doc.copy()
                result_doc["retrieval_score"] = float(final_score)
                result_doc["semantic_score"] = float(dict(semantic_results).get(idx, 0))
                result_doc["keyword_score"] = float(dict(keyword_results).get(idx, 0))
                result_doc["authority_boost"] = float(authority_boost)
                result_doc["topic_boost"] = float(type_boost)
                result_doc["title_boost"] = float(title_boost)
                final_results.append(result_doc)
        
        final_results.sort(key=lambda x: x["retrieval_score"], reverse=True)
        
        # Additional reranking for legal queries with section numbers
        if query_type == "COOPERATIVE_LAW":
            section_match = re.search(r'section\s*(\d+)', query.lower())
            if section_match:
                sec_num = section_match.group(1)
                for doc in final_results:
                    if sec_num in doc.get("chunk", "") or sec_num in doc.get("title", ""):
                        doc["retrieval_score"] += 0.3
                final_results.sort(key=lambda x: x["retrieval_score"], reverse=True)
        
        # Deduplicate by content and keep only top relevant
        # FIXED for upgraded DB: Allow multiple chunks with same title if different chunk_index (continuation chunks)
        # Group by title and allow up to 3 chunks per title for same question
        seen_titles_count = {}
        deduped_results = []
        for doc in final_results:
            title = doc.get("title", "")[:80]
            original_id = doc.get("original_id", "") or title
            chunk_idx = doc.get("chunk_index", -1)
            # Count how many times this title/original_id has appeared
            key = original_id or title
            count = seen_titles_count.get(key, 0)
            # Allow up to 4 chunks per same title/original_id (for upgraded DB friendly_answer that is chunked)
            # This ensures EMI definition chunk (idx 0) + continuation chunks (idx 6,7) can all be retrieved
            if count < 4:
                deduped_results.append(doc)
                seen_titles_count[key] = count + 1
            else:
                # For different titles, allow but limit total
                if title not in seen_titles_count or seen_titles_count.get(title, 0) < 2:
                    deduped_results.append(doc)
                    seen_titles_count[title] = seen_titles_count.get(title, 0) + 1
            if len(deduped_results) >= top_k:
                break
        
        top_results = deduped_results[:top_k]
        
        print(f"Retrieved {len(top_results)} docs (from {len(final_results)} above threshold, {len(combined_scores)} combined)")
        for i, doc in enumerate(top_results[:3]):
            print(f"  {i+1}. Score: {doc['retrieval_score']:.3f} (topic+{doc.get('topic_boost',0):.2f} auth+{doc.get('authority_boost',0):.2f} title+{doc.get('title_boost',0):.2f}) - {doc.get('title','')[:60]} idx {doc.get('chunk_index',-1)}")
        
        return top_results
    
    def get_status(self) -> Dict:
        return {
            "total_documents": len(self.documents),
            "use_faiss": self.use_faiss,
            "use_transformer": self.embedding_model.use_transformer if self.embedding_model else False,
            "has_embeddings": self.embeddings is not None or self.faiss_index is not None,
            "has_tfidf": self.tfidf_matrix is not None,
            "data_dir": str(self.data_dir)
        }

_retriever_instance = None

def get_retriever() -> HybridRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HybridRetriever()
    return _retriever_instance
