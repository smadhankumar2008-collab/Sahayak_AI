"""
Embeddings handling with fallback to TF-IDF
Supports sentence-transformers if available, else TF-IDF for offline prototype
"""
import os
import pickle
import json
from typing import List, Optional, Tuple
import numpy as np

class EmbeddingModel:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.model = None
        self.use_transformer = False
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        
        # Try to load sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            print(f"Loading embedding model: {self.model_name}")
            # For offline, try smaller model first if large fails
            try:
                self.model = SentenceTransformer(self.model_name)
                self.use_transformer = True
                print(f"Successfully loaded transformer model: {self.model_name}")
            except Exception as e:
                print(f"Failed to load {self.model_name}: {e}")
                # Try fallback model
                fallback = "sentence-transformers/all-MiniLM-L6-v2"
                print(f"Trying fallback: {fallback}")
                try:
                    self.model = SentenceTransformer(fallback)
                    self.use_transformer = True
                    print(f"Loaded fallback model: {fallback}")
                except Exception as e2:
                    print(f"Fallback also failed: {e2}, using TF-IDF")
                    self.use_transformer = False
        except ImportError:
            print("sentence-transformers not available, using TF-IDF")
            self.use_transformer = False
        except Exception as e:
            print(f"Error loading embedding model: {e}, using TF-IDF")
            self.use_transformer = False
    
    def fit_tfidf(self, texts: List[str]):
        """Fit TF-IDF vectorizer on texts"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95
            )
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            print(f"TF-IDF fitted on {len(texts)} documents, vocab size: {len(self.tfidf_vectorizer.vocabulary_)}")
        except Exception as e:
            print(f"TF-IDF fitting failed: {e}")
            # Simple fallback
            self.tfidf_vectorizer = None
    
    def encode(self, texts: List[str], show_progress: bool = False) -> np.ndarray:
        """Encode texts to embeddings"""
        if self.use_transformer and self.model is not None:
            try:
                embeddings = self.model.encode(texts, show_progress_bar=show_progress, convert_to_numpy=True, normalize_embeddings=True)
                return embeddings.astype('float32')
            except Exception as e:
                print(f"Transformer encoding failed: {e}, falling back to TF-IDF")
                self.use_transformer = False
        
        # TF-IDF fallback
        if self.tfidf_vectorizer is not None:
            try:
                vectors = self.tfidf_vectorizer.transform(texts)
                # Convert to dense and normalize
                dense = vectors.toarray()
                # L2 normalize
                norms = np.linalg.norm(dense, axis=1, keepdims=True)
                norms[norms == 0] = 1
                dense = dense / norms
                return dense
            except Exception as e:
                print(f"TF-IDF encoding failed: {e}")
        
        # Last resort: simple hash-based embeddings (for testing)
        print("Using hash-based fallback embeddings")
        return self._hash_embeddings(texts)
    
    def _hash_embeddings(self, texts: List[str], dim: int = 384) -> np.ndarray:
        """Simple hash-based embeddings as last resort"""
        embeddings = []
        for text in texts:
            # Create deterministic pseudo-embedding from text hash
            import hashlib
            # Use multiple hashes to fill dimensions
            vec = np.zeros(dim)
            for i in range(dim):
                h = hashlib.md5(f"{text}{i}".encode()).hexdigest()
                # Convert hex to float between -1 and 1
                val = (int(h[:8], 16) % 1000) / 500.0 - 1.0
                vec[i] = val
            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec)
        return np.array(embeddings)
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode single text"""
        return self.encode([text])[0]

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity"""
    if a.ndim == 1 and b.ndim == 1:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
    # For matrices
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8) if b.ndim > 1 else b / (np.linalg.norm(b) + 1e-8)
    return np.dot(a_norm, b_norm.T)

def load_or_create_embeddings(documents: List[dict], embedding_model: EmbeddingModel, cache_path: str = None) -> Tuple[np.ndarray, List[dict]]:
    """
    Create embeddings for documents
    Returns (embeddings, documents)
    """
    texts = [doc.get("chunk", doc.get("summary", doc.get("title", ""))) for doc in documents]
    
    # Fit TF-IDF if not using transformer
    if not embedding_model.use_transformer:
        embedding_model.fit_tfidf(texts)
    
    print(f"Encoding {len(texts)} documents...")
    embeddings = embedding_model.encode(texts, show_progress=True)
    print(f"Embeddings shape: {embeddings.shape}")
    
    return embeddings, documents
