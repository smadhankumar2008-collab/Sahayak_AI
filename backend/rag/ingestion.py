"""
Knowledge Base Ingestion for Sahayak AI - FIXED for deduplication and cleaning
- Removes duplicate content
- Removes boilerplate
- Preserves title, URL, section info
- Better chunking
"""
import json
import os
import hashlib
import pickle
import time
import re
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np

from .url_loader import chunk_text, process_urls_from_knowledge_base, fetch_url_content
from .embeddings import EmbeddingModel, load_or_create_embeddings

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_PATH = BASE_DIR.parent / "knowledge" / "knowledge_base.json"
if not KNOWLEDGE_PATH.exists():
    KNOWLEDGE_PATH = Path(__file__).parent.parent.parent / "knowledge" / "knowledge_base.json"
if not KNOWLEDGE_PATH.exists():
    KNOWLEDGE_PATH = Path("/home/user/sahayak-ai/knowledge/knowledge_base.json")

DATA_DIR.mkdir(exist_ok=True)

def load_knowledge_base(path: Path = None) -> dict:
    kb_path = path or KNOWLEDGE_PATH
    print(f"Loading knowledge base from: {kb_path}")
    if not kb_path.exists():
        raise FileNotFoundError(f"Knowledge base not found at {kb_path}")
    with open(kb_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded KB with keys: {list(data.keys())}")
    return data

def clean_chunk_text(text: str) -> str:
    """Remove boilerplate, navigation, duplicate headers"""
    if not text:
        return ""
    # Remove common boilerplate patterns
    boilerplate_patterns = [
        r'Home\s*>\s*.*',
        r'Navigation Menu',
        r'Skip to main content',
        r'Copyright.*\d{4}',
        r'All rights reserved',
        r'Click here to.*',
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove very short lines that are likely nav
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        if len(line) < 5:
            continue
        # Skip lines that are just navigation
        if len(line.split()) <= 2 and len(line) < 25:
            important = ["pacs", "pmfby", "cooperative", "scheme", "act", "section", "rights", "member", "grievance"]
            if not any(kw in line.lower() for kw in important):
                continue
        cleaned.append(line)
    
    text = '\n'.join(cleaned)
    return text.strip()

def flatten_knowledge_base(kb_data: dict) -> List[Dict]:
    documents = []
    seen_content_hashes = set()
    
    categories = {
        "cooperative_laws": "COOPERATIVE_LAW",
        "government_schemes": "GOVERNMENT_SCHEME", 
        "pacs_services": "PACS_SERVICE",
        "crop_insurance": "CROP_INSURANCE",
        "crop_insurance_other_schemes": "CROP_INSURANCE",
        "financial_literacy": "FINANCIAL_LITERACY",
        "grievance_redressal": "GRIEVANCE_REDDRESSAL",
        "national_cooperative_federations": "GENERAL_COOPERATIVE",
        "glossary": "GENERAL_COOPERATIVE",
        "helplines_quick_reference": "GENERAL_COOPERATIVE"
    }
    
    if "state_cooperative_registrars" in kb_data:
        registrars = kb_data["state_cooperative_registrars"]
        if isinstance(registrars, dict) and "entries" in registrars:
            entries = registrars["entries"]
            if isinstance(entries, dict):
                for state, info in entries.items():
                    if isinstance(info, dict):
                        text = f"Registrar of Cooperative Societies for {state}: {json.dumps(info, ensure_ascii=False)}"
                        content_hash = hashlib.md5(text.encode()).hexdigest()
                        if content_hash in seen_content_hashes:
                            continue
                        seen_content_hashes.add(content_hash)
                        doc = {
                            "id": f"registrar-{state.lower().replace(' ', '-')}",
                            "chunk": clean_chunk_text(text),
                            "title": f"Cooperative Registrar - {state}",
                            "summary": f"Contact for Registrar of Cooperative Societies in {state}",
                            "category": "LAW",
                            "query_type": "COOPERATIVE_LAW",
                            "source_name": registrars.get("source_name", "crcs.gov.in"),
                            "source_url": registrars.get("source_url", "https://www.crcs.gov.in"),
                            "authority": "State Registrar",
                            "state": state,
                            "type": "registrar"
                        }
                        documents.append(doc)
    
    for kb_key, query_type in categories.items():
        if kb_key not in kb_data:
            continue
        entries = kb_data[kb_key]
        if not isinstance(entries, list):
            continue
        
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            
            # Skip entries that are clearly unrelated or duplicate internship that causes contamination
            # But keep them if they are actually about PACS services
            title = entry.get("title", entry.get("id", ""))
            # For government_schemes, skip internship scheme if it's causing contamination for PACS queries
            # We'll keep it but mark with lower priority - it will be filtered in retrieval
            # Actually keep all but ensure clean
            
            parts = []
            if title:
                parts.append(f"Title: {title}")
            
            # CRITICAL: friendly_answer is highest priority for upgraded DB - contains detailed answer for 34 Qs
            if "friendly_answer" in entry and entry["friendly_answer"]:
                parts.append(f"Answer: {entry['friendly_answer']}")
            
            for field in ["summary", "description", "beneficiary", "how_to_access", "applicable_to"]:
                if field in entry and entry[field]:
                    val = entry[field]
                    if isinstance(val, str):
                        parts.append(f"{field.replace('_', ' ').title()}: {val}")
            
            if "key_points" in entry and entry["key_points"]:
                kp = entry["key_points"]
                if isinstance(kp, list):
                    parts.append("Key Points: " + "; ".join(kp))
                elif isinstance(kp, str):
                    parts.append(f"Key Points: {kp}")
            
            for field in ["how_to_use", "timelines", "helpline", "portal", "benefits", "procedure", "eligibility", "coverage", "documents_required", "process", "checklist"]:
                if field in entry and entry[field]:
                    val = entry[field]
                    if isinstance(val, list):
                        parts.append(f"{field.title()}: " + "; ".join(str(x) for x in val))
                    elif isinstance(val, str):
                        parts.append(f"{field.title()}: {val}")
            
            full_text = "\n".join(parts)
            if not full_text.strip():
                full_text = json.dumps(entry, ensure_ascii=False)
            
            full_text = clean_chunk_text(full_text)
            
            # Check duplicate
            content_hash = hashlib.md5(full_text.encode()).hexdigest()
            if content_hash in seen_content_hashes:
                continue
            seen_content_hashes.add(content_hash)
            
            chunks = chunk_text(full_text, chunk_size=500, overlap=80)
            
            for idx, chunk in enumerate(chunks):
                chunk = clean_chunk_text(chunk)
                if len(chunk) < 50:
                    continue
                # Deduplicate chunks
                chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
                if chunk_hash in seen_content_hashes:
                    continue
                seen_content_hashes.add(chunk_hash)
                
                doc = {
                    "id": f"{entry.get('id', kb_key)}-chunk-{idx}",
                    "chunk": chunk,
                    "title": title,
                    "summary": entry.get("summary", "")[:500],
                    "category": kb_key,
                    "query_type": query_type,
                    "source_name": entry.get("source_name", "Government Source"),
                    "source_url": entry.get("source_url", ""),
                    "authority": entry.get("source_name", "Official"),
                    "type": "knowledge_base",
                    "chunk_index": idx,
                    "original_id": entry.get("id", ""),
                    "content_hash": chunk_hash,
                    "metadata": {
                        "last_verified": entry.get("last_verified", ""),
                    }
                }
                for extra in ["beneficiary", "portal", "helpline"]:
                    if extra in entry:
                        doc[extra] = entry[extra]
                documents.append(doc)
    
    print(f"Flattened KB into {len(documents)} deduped chunked documents (from {len(seen_content_hashes)} unique hashes)")
    return documents

def ingest_knowledge_base(fetch_urls: bool = False, max_urls: int = 10, embedding_model_name: str = None) -> Dict:
    start_time = time.time()
    kb_data = load_knowledge_base()
    kb_documents = flatten_knowledge_base(kb_data)
    
    url_documents = []
    failed_urls = []
    if fetch_urls:
        print("Fetching official URLs...")
        try:
            url_docs = process_urls_from_knowledge_base(kb_data, max_urls=max_urls)
            # Clean URL docs
            cleaned_url_docs = []
            seen_hashes = set()
            for doc in url_docs:
                chunk = clean_chunk_text(doc.get("chunk", ""))
                if len(chunk) < 50:
                    continue
                h = hashlib.md5(chunk.encode()).hexdigest()
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                doc["chunk"] = chunk
                doc["content_hash"] = h
                cleaned_url_docs.append(doc)
            url_documents = cleaned_url_docs
            print(f"Fetched {len(url_documents)} cleaned documents from URLs")
        except Exception as e:
            print(f"URL fetching failed: {e}")
            failed_urls.append(str(e))
    
    all_documents = kb_documents + url_documents
    print(f"Total documents for embedding: {len(all_documents)}")
    
    print("Initializing embedding model...")
    embed_model = EmbeddingModel(model_name=embedding_model_name)
    texts = [doc["chunk"] for doc in all_documents]
    if not embed_model.use_transformer:
        embed_model.fit_tfidf(texts)
    
    print("Generating embeddings...")
    embeddings = embed_model.encode(texts, show_progress=True)
    
    try:
        import faiss
        dimension = embeddings.shape[1]
        print(f"Creating FAISS index with dimension {dimension}")
        embeddings = embeddings.astype('float32')
        embeddings = np.ascontiguousarray(embeddings)
        try:
            faiss.normalize_L2(embeddings)
        except Exception as e:
            print(f"FAISS normalize failed {e}, manual normalize")
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1
            embeddings = embeddings / norms
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        index_path = DATA_DIR / "vector_store.faiss"
        faiss.write_index(index, str(index_path))
        print(f"FAISS index saved to {index_path}, total vectors: {index.ntotal}")
    except ImportError:
        print("FAISS not available, saving embeddings as numpy file")
        index_path = DATA_DIR / "vector_store.npy"
        np.save(str(index_path), embeddings)
        with open(DATA_DIR / "faiss_meta.json", "w") as f:
            json.dump({"dimension": embeddings.shape[1], "count": embeddings.shape[0]}, f)
    
    metadata_path = DATA_DIR / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(all_documents, f, ensure_ascii=False, indent=2)
    
    model_info = {
        "model_name": embed_model.model_name,
        "use_transformer": embed_model.use_transformer,
        "dimension": embeddings.shape[1],
        "total_documents": len(all_documents),
        "kb_documents": len(kb_documents),
        "url_documents": len(url_documents),
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "failed_urls": failed_urls,
        "knowledge_base_version": kb_data.get("metadata", {}).get("version", "unknown")
    }
    
    with open(DATA_DIR / "ingestion_info.json", 'w', encoding='utf-8') as f:
        json.dump(model_info, f, ensure_ascii=False, indent=2)
    
    if not embed_model.use_transformer and embed_model.tfidf_vectorizer is not None:
        import pickle
        with open(DATA_DIR / "tfidf_vectorizer.pkl", 'wb') as f:
            pickle.dump(embed_model.tfidf_vectorizer, f)
    
    elapsed = time.time() - start_time
    print(f"Ingestion completed in {elapsed:.2f}s")
    print(f"Documents: {len(all_documents)}, Embeddings: {embeddings.shape}")
    
    return {
        "total_documents": len(all_documents),
        "kb_documents": len(kb_documents),
        "url_documents": len(url_documents),
        "dimension": embeddings.shape[1],
        "elapsed_seconds": elapsed,
        "model_info": model_info
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest knowledge base for Sahayak AI")
    parser.add_argument("--fetch-urls", action="store_true", help="Fetch official URLs")
    parser.add_argument("--max-urls", type=int, default=10, help="Max URLs to fetch")
    parser.add_argument("--model", type=str, default=None, help="Embedding model name")
    args = parser.parse_args()
    result = ingest_knowledge_base(fetch_urls=args.fetch_urls, max_urls=args.max_urls, embedding_model_name=args.model)
    print(json.dumps(result, indent=2))
