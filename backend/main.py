"""
Sahayak AI - FastAPI Backend - CRITICAL LANGUAGE LOCK FIX
SIH 26088 - SELECTED LANGUAGE = RESPONSE LANGUAGE (Single Source of Truth)
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Setup logging for language debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sahayak.api")

from backend.rag.retrieval import get_retriever, HybridRetriever
from backend.rag.ingestion import ingest_knowledge_base, load_knowledge_base
from backend.chatbot.language import (
    detect_language, classify_query_domain, LANGUAGE_CONFIG, 
    get_language_config, get_llm_instruction, get_report_labels,
    get_strict_language_prompt, is_response_in_selected_language,
    get_language_badge, get_fallback_error_message
)
from backend.chatbot.generator import generate_answer
from backend.chatbot.guardrails import get_evidence_level

app = FastAPI(
    title="Sahayak AI - Cooperative Compliance Co-Pilot",
    description="Multilingual Cooperative Governance & Legal Assistance Chatbot - SIH 26088 - Language Lock Fix",
    version="3.0.0 - LANGUAGE LOCK"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever: Optional[HybridRetriever] = None

def get_retriever_instance():
    global retriever
    if retriever is None:
        retriever = get_retriever()
    return retriever

class ChatRequest(BaseModel):
    question: str
    language: str = "en"  # SELECTED LANGUAGE - SINGLE SOURCE OF TRUTH - HIGHEST PRIORITY
    message: Optional[str] = None  # Alternative field name
    session_id: str = "default"
    history: List[Dict] = []
    top_k: int = 6
    conversation_language: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict]
    detected_language: str
    selected_language: str
    query_type: str
    evidence_level: str
    grounded: bool
    retrieval_scores: List[float] = []
    generation_method: str = "extractive"
    timestamp: str
    tts_language: str
    ttsLanguage: str = ""  # For frontend compatibility
    language: str = ""  # Selected language
    language_badge: str = ""  # 🌐 தமிழ்
    llm_instruction_used: str = ""
    language_valid: bool = True
    detected_response_language: str = ""

class LanguageDetectRequest(BaseModel):
    text: str
    selected_language: str = "en"

@app.get("/")
async def root(request: Request):
    frontend_index = Path(__file__).parent.parent / "frontend" / "index.html"
    accept = request.headers.get("accept", "")
    if frontend_index.exists() and ("text/html" in accept or "*/*" in accept or "text/html" in str(request.headers.get("accept", "")) or request.headers.get("sec-fetch-dest") == "document"):
        return FileResponse(str(frontend_index))
    # Also serve frontend for root without accept header check for browser
    if frontend_index.exists():
        # Check if user agent is browser
        ua = request.headers.get("user-agent", "").lower()
        if "mozilla" in ua or "chrome" in ua or "safari" in ua or "edge" in ua:
            return FileResponse(str(frontend_index))
    return {
        "message": "Sahayak AI - Cooperative Compliance Co-Pilot - LANGUAGE LOCK FIX",
        "version": "3.0.0",
        "problem_statement": "SIH26088",
        "status": "running",
        "language_lock": "SELECTED LANGUAGE = RESPONSE LANGUAGE - Single Source of Truth",
        "language_priority": "selectedLanguage is ONLY authority - Manual selected > everything",
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health",
            "status": "/api/status",
            "languages": "/api/languages",
            "ingest": "/api/ingest",
            "frontend": "/app"
        }
    }

@app.get("/api/health")
async def health():
    ret = get_retriever_instance()
    status = ret.get_status()
    return {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "retriever": status,
        "llm_available": bool(os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")),
        "language_lock": "SELECTED LANGUAGE = RESPONSE LANGUAGE",
        "language_priority": "selectedLanguage is ONLY authority"
    }

@app.get("/api/status")
async def get_status():
    ret = get_retriever_instance()
    status = ret.get_status()
    info_path = Path(__file__).parent / "data" / "ingestion_info.json"
    ingestion_info = {}
    if info_path.exists():
        try:
            with open(info_path, 'r') as f:
                ingestion_info = json.load(f)
        except:
            pass
    kb_path = Path(__file__).parent.parent / "knowledge" / "knowledge_base.json"
    kb_exists = kb_path.exists()
    kb_size = kb_path.stat().st_size if kb_exists else 0
    return {
        "knowledge_base": {"exists": kb_exists, "size_bytes": kb_size, "path": str(kb_path)},
        "vector_store": status,
        "ingestion": ingestion_info,
        "languages": list(LANGUAGE_CONFIG.keys()),
        "language_lock": "SELECTED = RESPONSE",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

@app.get("/api/languages")
async def get_languages():
    return {
        "languages": LANGUAGE_CONFIG,
        "supported": list(LANGUAGE_CONFIG.keys()),
        "default": "en",
        "priority": "SELECTED LANGUAGE = RESPONSE LANGUAGE - selectedLanguage is ONLY authority",
        "language_lock": "USER SELECTS LANGUAGE → selectedLanguage → RAG → LLM → RESPONSE IN selectedLanguage → TTS IN selectedLanguage"
    }

@app.post("/api/detect-language")
async def detect_lang(request: LanguageDetectRequest):
    detected = detect_language(request.text, request.selected_language)
    config = get_language_config(detected)
    selected_config = get_language_config(request.selected_language)
    final_language = request.selected_language if request.selected_language in LANGUAGE_CONFIG else detected
    return {
        "text": request.text[:200],
        "detected_language": detected,
        "selected_language": request.selected_language,
        "final_language": final_language,
        "language_name": config["name"],
        "native_name": config["nativeName"],
        "selected_language_instruction": selected_config.get("llm_instruction", ""),
        "priority": "selected > detected - SELECTED is authority"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    CRITICAL LANGUAGE LOCK FIX
    SELECTED LANGUAGE = RESPONSE LANGUAGE - Single Source of Truth
    
    Data Flow:
    USER SELECTS LANGUAGE → selectedLanguage → CHAT REQUEST → BACKEND → RAG → LLM → RESPONSE IN selectedLanguage → TTS IN selectedLanguage
    """
    # Handle both 'question' and 'message' fields
    question_text = request.question or request.message or ""
    if not question_text or not question_text.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(question_text) > 2000:
        raise HTTPException(status_code=400, detail="Question too long (max 2000 chars)")
    
    # ===== STEP 1: SINGLE SOURCE OF TRUTH - SELECTED LANGUAGE =====
    # Backend MUST trust selected language from frontend
    # Do NOT use detected language as final response language
    raw_selected = request.language or "en"
    
    # Ensure selected language is valid - if not, use en only as default when user actually selected en or invalid
    # NEVER fallback to en when user selected ta, hi, etc.
    if raw_selected not in LANGUAGE_CONFIG:
        print(f"[LANGUAGE LOCK] WARNING: Invalid selected language '{raw_selected}', checking alternatives")
        # Try to handle full locale codes like ta-IN -> ta
        if "-" in raw_selected:
            base_lang = raw_selected.split("-")[0]
            if base_lang in LANGUAGE_CONFIG:
                raw_selected = base_lang
                print(f"[LANGUAGE LOCK] Converted {request.language} -> {raw_selected}")
            else:
                raw_selected = "en"
        else:
            raw_selected = "en"
    
    # FINAL RESPONSE LANGUAGE IS ALWAYS THE SELECTED LANGUAGE - NO EXCEPTIONS
    selected_language = raw_selected
    response_language = selected_language  # SINGLE SOURCE OF TRUTH
    
    # Language detection ONLY for diagnostics, MUST NOT override selected
    detected_question_language = detect_language(question_text, selected_language)
    
    # Get language config - TTS MUST use same variable as LLM
    lang_config = get_language_config(response_language)
    tts_language = lang_config.get("ttsLanguage", lang_config.get("tts_code", f"{response_language}-IN"))
    strict_prompt = get_strict_language_prompt(response_language)
    language_badge = get_language_badge(response_language)
    
    # ===== DEBUGGING LOGS - As per requirement =====
    print(f"\n{'='*80}")
    print(f"[LANGUAGE LOCK DEBUG] ===== NEW REQUEST =====")
    print(f"[LANGUAGE LOCK DEBUG] Selected Language: {selected_language}")
    print(f"[LANGUAGE LOCK DEBUG] Language Name: {lang_config.get('name')} / {lang_config.get('nativeName')} ({language_badge})")
    print(f"[LANGUAGE LOCK DEBUG] Question: {question_text[:100]}")
    print(f"[LANGUAGE LOCK DEBUG] Detected Question Language (diagnostic only): {detected_question_language}")
    print(f"[LANGUAGE LOCK DEBUG] RAG Language: {response_language} (same as selected)")
    print(f"[LANGUAGE LOCK DEBUG] LLM Language: {response_language} (STRICT - MUST be {lang_config.get('nativeName')})")
    print(f"[LANGUAGE LOCK DEBUG] TTS Language: {tts_language} (same as selected)")
    print(f"[LANGUAGE LOCK DEBUG] Strict Prompt: {strict_prompt[:150]}...")
    print(f"[LANGUAGE LOCK DEBUG] Flow: USER SELECTS {selected_language} → selectedLanguage={selected_language} → RAG({response_language}) → LLM({response_language}) → RESPONSE({response_language}) → TTS({tts_language})")
    print(f"{'='*80}\n")
    
    logger.info(f"Selected: {selected_language}, Detected Q: {detected_question_language}, Final: {response_language}, TTS: {tts_language}, Q: {question_text[:50]}")
    
    # Step 2: Query Classification
    query_type = classify_query_domain(question_text)
    print(f"[LANGUAGE LOCK] Query classified as: {query_type} for language {response_language}")
    
    # Step 3: RAG Retrieval - RAG MUST NOT control language
    # Retrieved docs may be English, but response MUST be in selected language
    ret = get_retriever_instance()
    if not ret.documents:
        print("[LANGUAGE LOCK] No documents, attempting ingestion")
        try:
            ingest_knowledge_base(fetch_urls=False, max_urls=5)
            global retriever
            retriever = HybridRetriever()
            ret = retriever
        except Exception as e:
            print(f"Auto-ingestion failed: {e}")
    
    threshold = float(os.getenv("EVIDENCE_THRESHOLD", "0.20"))
    top_k = request.top_k or int(os.getenv("TOP_K", "6"))
    retrieve_k = min(top_k * 2, 12)
    
    try:
        evidence = ret.retrieve(
            query=question_text,
            top_k=retrieve_k,
            query_type=query_type,
            threshold=threshold
        )
        # Relevance filtering
        filtered_evidence = []
        for doc in evidence:
            doc_type = doc.get("query_type", "GENERAL_COOPERATIVE")
            score = doc.get("retrieval_score", 0)
            if query_type == doc_type:
                if score >= threshold:
                    filtered_evidence.append(doc)
            else:
                if score >= threshold + 0.15:
                    filtered_evidence.append(doc)
                elif query_type == "GENERAL_COOPERATIVE" and score >= threshold:
                    filtered_evidence.append(doc)
        
        filtered_evidence.sort(key=lambda x: x.get("retrieval_score", 0), reverse=True)
        evidence = filtered_evidence[:top_k]
        print(f"[LANGUAGE LOCK] After filtering: {len(evidence)} docs for {response_language} response (RAG may be English, but response MUST be {response_language})")
        
    except Exception as e:
        print(f"Retrieval failed: {e}")
        evidence = []
    
    avg_score = sum(doc.get("retrieval_score", 0) for doc in evidence) / len(evidence) if evidence else 0
    evidence_level = get_evidence_level(avg_score, len(evidence))
    
    # Step 4: LANGUAGE LOCK - Answer Generation in SELECTED language
    print(f"[LANGUAGE LOCK] Generating answer in SELECTED language: {response_language} (NOT detected {detected_question_language})")
    result = generate_answer(
        query=question_text,
        evidence=evidence,
        language=response_language,  # ALWAYS selected language - SINGLE SOURCE OF TRUTH
        query_type=query_type,
        history=request.history
    )
    
    # Step 5: RESPONSE LANGUAGE VALIDATION - As per requirement
    final_answer = result["answer"]
    is_valid, detected_response_lang, confidence = is_response_in_selected_language(final_answer, response_language)
    
    print(f"\n{'='*80}")
    print(f"[LANGUAGE LOCK VALIDATION] Selected: {response_language} ({lang_config.get('nativeName')})")
    print(f"[LANGUAGE LOCK VALIDATION] Response detected as: {detected_response_lang}")
    print(f"[LANGUAGE LOCK VALIDATION] Valid: {is_valid}, Confidence: {confidence:.2f}")
    print(f"[LANGUAGE LOCK VALIDATION] Answer preview: {final_answer[:100]}")
    print(f"[LANGUAGE LOCK VALIDATION] TTS will use: {tts_language} (same as selected)")
    print(f"{'='*80}\n")
    
    # If validation fails and selected is non-English, DO NOT return English
    # Retry logic is inside generator, but we add final check here
    if not is_valid and response_language != "en":
        print(f"[LANGUAGE LOCK CRITICAL] Response language validation FAILED - Selected {response_language} but got {detected_response_lang}")
        print(f"[LANGUAGE LOCK CRITICAL] Attempting to fix - will NOT return English when {response_language} selected")
        # If generator already tried retries and still failed, it returns fallback in selected language
        # If still English, force fallback error in selected language
        if detected_response_lang == "en":
            print(f"[LANGUAGE LOCK CRITICAL] Forcing fallback error message in {response_language} instead of English")
            final_answer = get_fallback_error_message(response_language)
            result["generation_method"] = "language_lock_error_fallback"
            result["grounded"] = False
    
    retrieval_scores = [doc.get("retrieval_score", 0) for doc in evidence]
    
    # Final debug log
    print(f"[LANGUAGE LOCK DEBUG FINAL] Selected: {selected_language}, Response Lang Validated: {response_language}, Detected Response: {detected_response_lang}, TTS: {tts_language}, Badge: {language_badge}")
    
    return ChatResponse(
        answer=final_answer,
        sources=result["sources"],
        detected_language=detected_question_language,
        selected_language=response_language,
        language=response_language,
        query_type=query_type,
        evidence_level=result.get("evidence_level", evidence_level),
        grounded=result.get("grounded", False),
        retrieval_scores=retrieval_scores,
        generation_method=result.get("generation_method", "extractive"),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        tts_language=tts_language,
        ttsLanguage=tts_language,
        language_badge=language_badge,
        llm_instruction_used=strict_prompt[:300] + "..." if len(strict_prompt) > 300 else strict_prompt,
        language_valid=is_valid,
        detected_response_language=detected_response_lang
    )

@app.post("/api/ingest")
async def trigger_ingest(fetch_urls: bool = False, max_urls: int = 10):
    try:
        result = ingest_knowledge_base(fetch_urls=fetch_urls, max_urls=max_urls)
        global retriever
        retriever = HybridRetriever()
        return {"status": "success", "message": "Knowledge base ingested", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    @app.get("/app")
    async def serve_frontend():
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"message": "Frontend not found"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
