"""
URL-aware loader for official government sources
Safe crawling with allowlist, cleaning, chunking
"""
import re
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import os

# Allowed domains for safety
DEFAULT_ALLOWED_DOMAINS = [
    "gov.in", "nic.in", "cooperation.gov.in", "pib.gov.in", 
    "nabard.org", "pmfby.gov.in", "myscheme.gov.in", 
    "indiacode.nic.in", "crcs.gov.in", "darpg.gov.in",
    "pgportal.gov.in", "ncdc.in", "agricoop.gov.in",
    "rbi.org.in", "ncf e.org.in", "data.gov.in"
]

def is_url_allowed(url: str, allowed_domains: List[str] = None) -> bool:
    """Check if URL is from allowed official domains"""
    if allowed_domains is None:
        allowed_str = os.getenv("ALLOWED_DOMAINS", "")
        if allowed_str:
            allowed_domains = [d.strip() for d in allowed_str.split(",")]
        else:
            allowed_domains = DEFAULT_ALLOWED_DOMAINS
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Allow if any allowed domain is substring of actual domain
        for allowed in allowed_domains:
            if allowed.lower() in domain:
                return True
        # Also allow if it's a gov domain pattern
        if domain.endswith(".gov.in") or domain.endswith(".nic.in"):
            return True
        return False
    except:
        return False

def validate_url_format(url: str) -> bool:
    """Basic URL format validation"""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"] and bool(parsed.netloc)
    except:
        return False

def fetch_url_content(url: str, timeout: int = 10) -> Tuple[Optional[str], Dict]:
    """
    Fetch URL content safely
    Returns (text, metadata)
    """
    metadata = {
        "source_url": url,
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "failed",
        "error": None,
        "content_hash": None,
        "title": None
    }
    
    if not validate_url_format(url):
        metadata["error"] = "Invalid URL format"
        return None, metadata
    
    # For prototype, we allow all URLs but log warning if not in allowlist
    if not is_url_allowed(url):
        metadata["warning"] = f"URL not in official allowlist: {url}"
        # Still try to fetch for prototype, but in production you might block
    
    try:
        headers = {
            "User-Agent": "SahayakAI/1.0 (SIH26088 Cooperative Chatbot; +https://cooperation.gov.in) Educational/Research"
        }
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "")
        
        # Handle PDF
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            text = extract_pdf_text(response.content, url)
        else:
            # HTML extraction
            text = extract_html_text(response.text, url)
            # Try to get title
            try:
                soup = BeautifulSoup(response.text, 'lxml')
                title_tag = soup.find('title')
                if title_tag:
                    metadata["title"] = title_tag.get_text(strip=True)[:200]
            except:
                pass
        
        if not text or len(text.strip()) < 50:
            metadata["error"] = "No readable content extracted"
            return None, metadata
        
        # Generate content hash
        metadata["content_hash"] = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
        metadata["status"] = "success"
        metadata["content_length"] = len(text)
        
        return text, metadata
        
    except requests.exceptions.Timeout:
        metadata["error"] = "Request timeout"
        return None, metadata
    except requests.exceptions.RequestException as e:
        metadata["error"] = f"Request failed: {str(e)[:200]}"
        return None, metadata
    except Exception as e:
        metadata["error"] = f"Extraction failed: {str(e)[:200]}"
        return None, metadata

def extract_html_text(html: str, url: str = "") -> str:
    """Extract readable text from HTML, removing boilerplate"""
    try:
        # Try trafilatura first for better extraction
        try:
            import trafilatura
            extracted = trafilatura.extract(html, include_comments=False, include_tables=True)
            if extracted and len(extracted) > 100:
                return clean_text(extracted)
        except ImportError:
            pass
        except Exception:
            pass
        
        # Fallback to BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove unwanted tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
            tag.decompose()
        
        # Try to find main content
        main_content = None
        for selector in ["main", "article", "[role='main']", ".content", "#content", ".main-content"]:
            try:
                main_content = soup.select_one(selector)
                if main_content and len(main_content.get_text()) > 200:
                    break
            except:
                continue
        
        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)
        
        return clean_text(text)
    
    except Exception as e:
        return clean_text(html)[:5000]  # Fallback

def extract_pdf_text(content: bytes, url: str = "") -> str:
    """Extract text from PDF content"""
    try:
        import PyPDF2
        import io
        pdf_file = io.BytesIO(content)
        reader = PyPDF2.PdfReader(pdf_file)
        text_parts = []
        for i, page in enumerate(reader.pages[:20]):  # Limit to 20 pages for prototype
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"[Page {i+1}]\n{page_text}")
            except:
                continue
        return clean_text("\n\n".join(text_parts))
    except ImportError:
        return f"PDF content from {url} - PDF extraction not available (PyPDF2 not installed)"
    except Exception as e:
        return f"PDF extraction failed for {url}: {str(e)[:200]}"

def clean_text(text: str) -> str:
    """Clean extracted text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove very short lines that are likely nav items
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue
        # Skip lines that look like navigation
        if len(line.split()) <= 2 and len(line) < 20:
            # Could be nav, but keep if it contains important keywords
            important_keywords = ["pacs", "pmfby", "cooperative", "scheme", "act", "section"]
            if not any(kw in line.lower() for kw in important_keywords):
                # Check if it's likely nav - keep if longer
                if len(line) < 15:
                    continue
        cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    return text.strip()

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
    """Chunk text into overlapping pieces for RAG"""
    if not text:
        return []
    
    # Split by paragraphs first
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        # If paragraph itself is longer than chunk_size, split it
        if len(para) > chunk_size:
            # Split by sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sent in sentences:
                if len(current_chunk) + len(sent) + 1 <= chunk_size:
                    current_chunk += (" " + sent if current_chunk else sent)
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        # Overlap: take last overlap chars
                        current_chunk = current_chunk[-overlap:] + " " + sent if overlap > 0 else sent
                    else:
                        # Sentence longer than chunk_size, force split
                        for i in range(0, len(sent), chunk_size - overlap):
                            chunks.append(sent[i:i+chunk_size])
                        current_chunk = ""
            continue
        
        # Normal paragraph handling
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += ("\n\n" + para if current_chunk else para)
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + "\n\n" + para
                else:
                    current_chunk = para
            else:
                current_chunk = para
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Filter very short chunks
    chunks = [c for c in chunks if len(c.strip()) >= 50]
    
    return chunks

def process_urls_from_knowledge_base(kb_data: dict, max_urls: int = 20) -> List[Dict]:
    """
    Extract and process URLs from knowledge base
    Returns list of processed documents
    """
    urls_seen = set()
    documents = []
    
    # Collect all source_urls from KB
    def collect_urls(obj, category="unknown"):
        urls = []
        if isinstance(obj, dict):
            if "source_url" in obj and obj["source_url"]:
                urls.append((obj["source_url"], category, obj.get("title", ""), obj.get("source_name", "")))
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    urls.extend(collect_urls(v, category))
        elif isinstance(obj, list):
            for item in obj:
                urls.extend(collect_urls(item, category))
        return urls
    
    all_urls = []
    for category_key in ["cooperative_laws", "government_schemes", "pacs_services", "crop_insurance", "financial_literacy", "grievance_redressal"]:
        if category_key in kb_data:
            all_urls.extend(collect_urls(kb_data[category_key], category_key))
    
    # Deduplicate
    unique_urls = []
    for url, cat, title, authority in all_urls:
        if url not in urls_seen:
            urls_seen.add(url)
            unique_urls.append((url, cat, title, authority))
    
    # Limit for prototype
    unique_urls = unique_urls[:max_urls]
    
    print(f"Found {len(unique_urls)} unique URLs to process")
    
    for url, category, title, authority in unique_urls:
        print(f"Fetching: {url}")
        text, meta = fetch_url_content(url)
        if text:
            chunks = chunk_text(text, chunk_size=600, overlap=100)
            for i, chunk in enumerate(chunks[:5]):  # Limit chunks per URL for prototype
                doc = {
                    "id": f"url-{hashlib.md5((url+str(i)).encode()).hexdigest()[:8]}",
                    "chunk": chunk,
                    "source_url": url,
                    "source_title": meta.get("title") or title or url,
                    "authority": authority or "Official Government Source",
                    "category": category,
                    "retrieved_at": meta.get("retrieved_at"),
                    "content_hash": meta.get("content_hash"),
                    "type": "official_url",
                    "chunk_index": i
                }
                documents.append(doc)
        else:
            print(f"Failed to fetch {url}: {meta.get('error')}")
    
    return documents
