"""
Tests for Sahayak AI - SIH 26088
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.rag.retrieval import HybridRetriever
from backend.chatbot.language import detect_language, classify_query_domain
from backend.chatbot.generator import generate_answer
from backend.chatbot.guardrails import apply_guardrails

def test_language_detection():
    print("Testing language detection...")
    tests = [
        ("What is PACS?", "en"),
        ("ஒரு PACS-ல் உறுப்பினராக சேர என்ன ஆவணங்கள் தேவை?", "ta"),
        ("PACS का सदस्य बनने के लिए कौन से दस्तावेज़ आवश्यक हैं?", "hi"),
        ("ഒരു സഹകരണ സംഘത്തിൽ അംഗമാകാൻ ആവശ്യമായ രേഖകൾ ഏതൊക്കെയാണ്?", "ml"),
        ("PACS సభ్యుడిగా చేరడానికి ఏ పత్రాలు అవసరం?", "te"),
        ("PACS ಸದಸ್ಯರಾಗಲು ಯಾವ ದಾಖಲೆಗಳು ಅಗತ್ಯವಿದೆ?", "kn"),
        ("PACS चे सदस्य होण्यासाठी कोणती कागदपत्रे आवश्यक आहेत?", "mr"),
        ("PACS-এর সদস্য হতে কী কী নথি প্রয়োজন?", "bn"),
    ]
    for text, expected in tests:
        detected = detect_language(text, "en")
        status = "✅" if detected == expected else "❌"
        print(f"{status} '{text[:30]}...' -> {detected} (expected {expected})")

def test_query_routing():
    print("\nTesting query routing...")
    tests = [
        ("What is PMFBY?", "CROP_INSURANCE"),
        ("How to file grievance?", "GRIEVANCE"),
        ("What are board duties?", "LAW"),
        ("What documents for PACS?", "PACS"),
        ("What is Kisan Credit Card?", "PACS"),
    ]
    for q, expected in tests:
        routed = classify_query_domain(q)
        status = "✅" if routed == expected else "⚠️"
        print(f"{status} '{q}' -> {routed} (expected {expected})")

def test_hallucination_protection():
    print("\nTesting hallucination protection (critical)...")
    retriever = HybridRetriever()
    
    fake_queries = [
        "What is Section 999 of the Tamil Nadu Cooperative Societies Act?",
        "What is the XYZ Cooperative Scheme introduced in 2026?",
    ]
    
    for q in fake_queries:
        print(f"\nQuery: {q}")
        evidence = retriever.retrieve(q, top_k=3)
        result = generate_answer(q, evidence, language="en", query_type="LAW")
        answer = result["answer"]
        
        # Should return fallback, not hallucinate
        is_fallback = "could not find sufficient" in answer.lower() or "not found" in answer.lower() or "போதுமான" in answer
        if is_fallback:
            print(f"✅ Correctly returned fallback (no hallucination)")
        else:
            print(f"❌ FAILED - Hallucinated answer: {answer[:200]}")
            # Check if it contains fabricated section
            if "999" in answer:
                print("❌ Contains fabricated Section 999!")

def test_retrieval():
    print("\nTesting RAG retrieval...")
    retriever = HybridRetriever()
    print(f"Total docs: {retriever.get_status()['total_documents']}")
    
    queries = [
        "What documents are required to join a PACS?",
        "What is PMFBY?",
        "How can I file a cooperative grievance?",
        "What are the rights of a cooperative member?",
        "What services are provided by PACS?",
    ]
    
    for q in queries:
        evidence = retriever.retrieve(q, top_k=3)
        print(f"\nQ: {q}")
        print(f"  Retrieved: {len(evidence)} docs")
        for ev in evidence[:2]:
            print(f"    - {ev['title'][:50]} (score {ev['retrieval_score']:.3f})")

def test_generation():
    print("\nTesting answer generation...")
    retriever = HybridRetriever()
    
    q = "What documents are required to join a PACS?"
    evidence = retriever.retrieve(q, top_k=4)
    result = generate_answer(q, evidence, language="en", query_type="PACS")
    
    print(f"\nQ: {q}")
    print(f"Answer: {result['answer'][:500]}")
    print(f"Evidence level: {result['evidence_level']}")
    print(f"Sources: {len(result['sources'])}")
    
    # Check for required elements
    has_docs = any(word in result['answer'].lower() for word in ['identity', 'aadhaar', 'address', 'document'])
    print(f"Contains document info: {'✅' if has_docs else '❌'}")

if __name__ == "__main__":
    print("="*60)
    print("Sahayak AI - Test Suite")
    print("="*60)
    
    test_language_detection()
    test_query_routing()
    test_retrieval()
    test_generation()
    test_hallucination_protection()
    
    print("\n" + "="*60)
    print("Tests completed")
    print("="*60)
