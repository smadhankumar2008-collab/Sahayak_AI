#!/usr/bin/env python3
"""
Knowledge ingestion script for Sahayak AI
Usage: python scripts/ingest.py [--fetch-urls] [--max-urls 10]
"""
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.rag.ingestion import ingest_knowledge_base

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest knowledge base for Sahayak AI")
    parser.add_argument("--fetch-urls", action="store_true", help="Fetch official URLs (requires internet)")
    parser.add_argument("--max-urls", type=int, default=10, help="Max URLs to fetch")
    parser.add_argument("--model", type=str, default=None, help="Embedding model name")
    args = parser.parse_args()
    
    print("="*60)
    print("Sahayak AI - Knowledge Base Ingestion")
    print("="*60)
    print(f"Fetch URLs: {args.fetch_urls}")
    print(f"Max URLs: {args.max_urls}")
    print(f"Model: {args.model or 'default (TF-IDF fallback if transformers unavailable)'}")
    print()
    
    try:
        result = ingest_knowledge_base(
            fetch_urls=args.fetch_urls,
            max_urls=args.max_urls,
            embedding_model_name=args.model
        )
        print()
        print("="*60)
        print("Ingestion Completed Successfully!")
        print("="*60)
        print(f"Total documents: {result['total_documents']}")
        print(f"KB documents: {result['kb_documents']}")
        print(f"URL documents: {result['url_documents']}")
        print(f"Embedding dimension: {result['dimension']}")
        print(f"Time taken: {result['elapsed_seconds']:.2f}s")
    except Exception as e:
        print(f"Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
