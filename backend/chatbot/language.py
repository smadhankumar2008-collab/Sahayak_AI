"""
Language configuration and detection for Sahayak AI
Supports 8 languages: en, ta, hi, ml, te, kn, mr, bn
Centralized config with STT/TTS identifiers and LLM instructions
Selected language has highest priority
"""
import re
from typing import Dict, Optional

# Centralized language configuration as per requirements
LANGUAGE_CONFIG = {
    "en": {
        "code": "en",
        "name": "English",
        "nativeName": "English",
        "flag": "🇮🇳",
        # STT/TTS identifiers - Web Speech API compatible
        "stt_code": "en-IN",
        "tts_code": "en-IN",
        "tts_lang": "en-IN",
        "speechRecognition": "en-IN",
        "ttsLanguage": "en-IN",
        "bcp47": "en-IN",
        "voice_names": ["English", "en-IN", "English India"],
        "instruction": "Respond only in English. Answer the user's question in natural English using the retrieved evidence.",
        "llm_instruction": "The user has selected English. Answer ONLY in English. Use the retrieved knowledge as factual source. Do not translate to other languages. Preserve official names, law names, scheme names accurately.",
        "fallback_message": "I could not find sufficient information in the verified knowledge sources to answer this accurately. Please refer to the cited official source or contact the appropriate cooperative authority.",
        "listening_text": "Listening...",
        "processing_text": "Processing...",
        "report_title": "SAHAYAK AI - Cooperative Compliance Report",
        "report_query": "User Query",
        "report_answer": "AI Response",
        "report_sources": "Sources",
        "report_date": "Date",
        "report_language": "Language",
        "suggested": [
            "What documents are required to join a PACS?",
            "What is PMFBY?",
            "How can I file a cooperative grievance?",
            "What are the rights of a cooperative member?",
            "What services are provided by PACS?"
        ]
    },
    "ta": {
        "code": "ta",
        "name": "Tamil",
        "nativeName": "தமிழ்",
        "flag": "🇮🇳",
        "stt_code": "ta-IN",
        "tts_code": "ta-IN",
        "tts_lang": "ta-IN",
        "speechRecognition": "ta-IN",
        "ttsLanguage": "ta-IN",
        "bcp47": "ta-IN",
        "voice_names": ["Tamil", "ta-IN", "Tamil India"],
        "instruction": "பயனர் கேள்விக்கு தமிழில் மட்டும் பதிலளிக்கவும். மீட்டெடுக்கப்பட்ட ஆதாரங்களைப் பயன்படுத்தி இயற்கையான தமிழில் பதிலளிக்கவும்.",
        "llm_instruction": "The user has selected Tamil (தமிழ்). Answer ONLY in Tamil. Use the retrieved knowledge as factual source. Do not answer in English unless user explicitly requests English. Preserve official names like PMFBY, PACS, Acts accurately - keep English names but explain in Tamil. If technical terms have no natural Tamil translation, retain official term and explain in Tamil.",
        "fallback_message": "இந்த கேள்விக்கு துல்லியமாக பதிலளிக்க போதுமான தகவல் சரிபார்க்கப்பட்ட அறிவு ஆதாரங்களில் கிடைக்கவில்லை. குறிப்பிடப்பட்ட அதிகாரப்பூர்வ ஆதாரத்தைப் பார்க்கவும் அல்லது தகுந்த கூட்டுறவு அதிகாரியைத் தொடர்பு கொள்ளவும்.",
        "listening_text": "கேட்கிறது...",
        "processing_text": "செயலாக்குகிறது...",
        "report_title": "சஹாயக் AI - கூட்டுறவு இணக்க அறிக்கை",
        "report_query": "பயனர் கேள்வி",
        "report_answer": "AI பதில்",
        "report_sources": "ஆதாரங்கள்",
        "report_date": "தேதி",
        "report_language": "மொழி",
        "suggested": [
            "ஒரு PACS-ல் உறுப்பினராக சேர என்ன ஆவணங்கள் தேவை?",
            "PMFBY என்றால் என்ன?",
            "கூட்டுறவு புகாரை எவ்வாறு தாக்கல் செய்வது?",
            "கூட்டுறவு உறுப்பினரின் உரிமைகள் என்ன?",
            "PACS வழங்கும் சேவைகள் என்ன?"
        ]
    },
    "hi": {
        "code": "hi",
        "name": "Hindi",
        "nativeName": "हिन्दी",
        "flag": "🇮🇳",
        "stt_code": "hi-IN",
        "tts_code": "hi-IN",
        "tts_lang": "hi-IN",
        "speechRecognition": "hi-IN",
        "ttsLanguage": "hi-IN",
        "bcp47": "hi-IN",
        "voice_names": ["Hindi", "hi-IN", "Hindi India"],
        "instruction": "केवल हिन्दी में उत्तर दें। प्राप्त साक्ष्य का उपयोग करके स्वाभाविक हिन्दी में उत्तर दें।",
        "llm_instruction": "The user has selected Hindi (हिन्दी). Answer ONLY in Hindi. Use the retrieved knowledge as factual source. Do not answer in English. Preserve official names like PMFBY, PACS, Acts accurately - keep English names but explain in Hindi.",
        "fallback_message": "इस प्रश्न का सटीक उत्तर देने के लिए सत्यापित ज्ञान स्रोतों में पर्याप्त जानकारी नहीं मिली। कृपया उद्धृत आधिकारिक स्रोत देखें या संबंधित सहकारी प्राधिकरण से संपर्क करें।",
        "listening_text": "सुन रहा है...",
        "processing_text": "प्रोसेस कर रहा है...",
        "report_title": "सहायक AI - सहकारी अनुपालन रिपोर्ट",
        "report_query": "उपयोगकर्ता प्रश्न",
        "report_answer": "AI उत्तर",
        "report_sources": "स्रोत",
        "report_date": "दिनांक",
        "report_language": "भाषा",
        "suggested": [
            "PACS का सदस्य बनने के लिए कौन से दस्तावेज़ आवश्यक हैं?",
            "PMFBY क्या है?",
            "सहकारी शिकायत कैसे दर्ज करें?",
            "सहकारी सदस्य के क्या अधिकार हैं?",
            "PACS द्वारा कौन सी सेवाएं प्रदान की जाती हैं?"
        ]
    },
    "ml": {
        "code": "ml",
        "name": "Malayalam",
        "nativeName": "മലയാളം",
        "flag": "🇮🇳",
        "stt_code": "ml-IN",
        "tts_code": "ml-IN",
        "tts_lang": "ml-IN",
        "speechRecognition": "ml-IN",
        "ttsLanguage": "ml-IN",
        "bcp47": "ml-IN",
        "voice_names": ["Malayalam", "ml-IN"],
        "instruction": "മലയാളത്തിൽ മാത്രം മറുപടി നൽകുക. വീണ്ടെടുത്ത തെളിവുകൾ ഉപയോഗിച്ച് സ്വാഭാവിക മലയാളത്തിൽ മറുപടി നൽകുക.",
        "llm_instruction": "The user has selected Malayalam (മലയാളം). Answer ONLY in Malayalam. Use retrieved knowledge as factual source. Do not answer in English. Preserve official names like PMFBY, PACS accurately.",
        "fallback_message": "ഈ ചോദ്യത്തിന് കൃത്യമായി ഉത്തരം നൽകാൻ പരിശോധിച്ചുറപ്പിച്ച വിജ്ഞാന സ്രോതസ്സുകളിൽ മതിയായ വിവരം കണ്ടെത്താനായില്ല. ദയവായി ഉദ്ധരിച്ച ഔദ്യോഗിക സ്രോതസ്സ് പരിശോധിക്കുകയോ ബന്ധപ്പെട്ട സഹകരണ അധികാരിയെ ബന്ധപ്പെടുകയോ ചെയ്യുക.",
        "listening_text": "കേൾക്കുന്നു...",
        "processing_text": "പ്രോസസ്സ് ചെയ്യുന്നു...",
        "report_title": "സഹായക് AI - സഹകരണ കംപ്ലയൻസ് റിപ്പോർട്ട്",
        "report_query": "ഉപയോക്തൃ ചോദ്യം",
        "report_answer": "AI മറുപടി",
        "report_sources": "ഉറവിടങ്ങൾ",
        "report_date": "തീയതി",
        "report_language": "ഭാഷ",
        "suggested": [
            "ഒരു സഹകരണ സംഘത്തിൽ അംഗമാകാൻ ആവശ്യമായ രേഖകൾ ഏതൊക്കെയാണ്?",
            "PMFBY എന്താണ്?",
            "സഹകരണ പരാതി എങ്ങനെ ഫയൽ ചെയ്യാം?",
            "സഹകരണ അംഗത്തിന്റെ അവകാശങ്ങൾ എന്തൊക്കെയാണ്?",
            "PACS നൽകുന്ന സേവനങ്ങൾ എന്തൊക്കെയാണ്?"
        ]
    },
    "te": {
        "code": "te",
        "name": "Telugu",
        "nativeName": "తెలుగు",
        "flag": "🇮🇳",
        "stt_code": "te-IN",
        "tts_code": "te-IN",
        "tts_lang": "te-IN",
        "speechRecognition": "te-IN",
        "ttsLanguage": "te-IN",
        "bcp47": "te-IN",
        "voice_names": ["Telugu", "te-IN"],
        "instruction": "తెలుగులో మాత్రమే సమాధానం ఇవ్వండి. తిరిగి పొందిన ఆధారాలను ఉపయోగించి సహజ తెలుగులో సమాధానం ఇవ్వండి.",
        "llm_instruction": "The user has selected Telugu (తెలుగు). Answer ONLY in Telugu. Use retrieved knowledge as factual source. Do not answer in English. Preserve official names like PMFBY, PACS accurately.",
        "fallback_message": "ఈ ప్రశ్నకు ఖచ్చితంగా సమాధానం ఇవ్వడానికి ధృవీకరించబడిన జ్ఞాన వనరులలో తగినంత సమాచారం కనుగొనబడలేదు. దయచేసి ఉదహరించిన అధికారిక మూలాన్ని చూడండి లేదా సంబంధిత సహకార అధికారాన్ని సంప్రదించండి.",
        "listening_text": "వింటోంది...",
        "processing_text": "ప్రాసెస్ చేస్తోంది...",
        "report_title": "సహాయక్ AI - సహకార సమ్మతి నివేదిక",
        "report_query": "వినియోగదారు ప్రశ్న",
        "report_answer": "AI సమాధానం",
        "report_sources": "మూలాలు",
        "report_date": "తేదీ",
        "report_language": "భాష",
        "suggested": [
            "PACS సభ్యుడిగా చేరడానికి ఏ పత్రాలు అవసరం?",
            "PMFBY అంటే ఏమిటి?",
            "సహకార ఫిర్యాదును ఎలా దాఖలు చేయాలి?",
            "సహకార సభ్యుని హక్కులు ఏమిటి?",
            "PACS అందించే సేవలు ఏమిటి?"
        ]
    },
    "kn": {
        "code": "kn",
        "name": "Kannada",
        "nativeName": "ಕನ್ನಡ",
        "flag": "🇮🇳",
        "stt_code": "kn-IN",
        "tts_code": "kn-IN",
        "tts_lang": "kn-IN",
        "speechRecognition": "kn-IN",
        "ttsLanguage": "kn-IN",
        "bcp47": "kn-IN",
        "voice_names": ["Kannada", "kn-IN"],
        "instruction": "ಕನ್ನಡದಲ್ಲಿ ಮಾತ್ರ ಉತ್ತರಿಸಿ. ಮರುಪಡೆಯಲಾದ ಪುರಾವೆಗಳನ್ನು ಬಳಸಿಕೊಂಡು ನೈಸರ್ಗಿಕ ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ.",
        "llm_instruction": "The user has selected Kannada (ಕನ್ನಡ). Answer ONLY in Kannada. Use retrieved knowledge as factual source. Do not answer in English. Preserve official names like PMFBY, PACS accurately.",
        "fallback_message": "ಈ ಪ್ರಶ್ನೆಗೆ ನಿಖರವಾಗಿ ಉತ್ತರಿಸಲು ಪರಿಶೀಲಿಸಿದ ಜ್ಞಾನ ಮೂಲಗಳಲ್ಲಿ ಸಾಕಷ್ಟು ಮಾಹಿತಿ ಸಿಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಉಲ್ಲೇಖಿಸಲಾದ ಅಧಿಕೃತ ಮೂಲವನ್ನು ನೋಡಿ ಅಥವಾ ಸಂಬಂಧಿತ ಸಹಕಾರಿ ಪ್ರಾಧಿಕಾರವನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        "listening_text": "ಆಲಿಸುತ್ತಿದೆ...",
        "processing_text": "ಸಂಸ್ಕರಿಸುತ್ತಿದೆ...",
        "report_title": "ಸಹಾಯಕ್ AI - ಸಹಕಾರಿ ಅನುಸರಣೆ ವರದಿ",
        "report_query": "ಬಳಕೆದಾರರ ಪ್ರಶ್ನೆ",
        "report_answer": "AI ಉತ್ತರ",
        "report_sources": "ಮೂಲಗಳು",
        "report_date": "ದಿನಾಂಕ",
        "report_language": "ಭಾಷೆ",
        "suggested": [
            "PACS ಸದಸ್ಯರಾಗಲು ಯಾವ ದಾಖಲೆಗಳು ಅಗತ್ಯವಿದೆ?",
            "PMFBY ಎಂದರೇನು?",
            "ಸಹಕಾರಿ ದೂರನ್ನು ಹೇಗೆ ಸಲ್ಲಿಸುವುದು?",
            "ಸಹಕಾರಿ ಸದಸ್ಯರ ಹಕ್ಕುಗಳು ಯಾವುವು?",
            "PACS ಒದಗಿಸುವ ಸೇವೆಗಳು ಯಾವುವು?"
        ]
    },
    "mr": {
        "code": "mr",
        "name": "Marathi",
        "nativeName": "मराठी",
        "flag": "🇮🇳",
        "stt_code": "mr-IN",
        "tts_code": "mr-IN",
        "tts_lang": "mr-IN",
        "speechRecognition": "mr-IN",
        "ttsLanguage": "mr-IN",
        "bcp47": "mr-IN",
        "voice_names": ["Marathi", "mr-IN"],
        "instruction": "फक्त मराठीत उत्तर द्या. पुनर्प्राप्त पुराव्यांचा वापर करून नैसर्गिक मराठीत उत्तर द्या.",
        "llm_instruction": "The user has selected Marathi (मराठी). Answer ONLY in Marathi. Use retrieved knowledge as factual source. Do not answer in English. Preserve official names like PMFBY, PACS accurately.",
        "fallback_message": "या प्रश्नाचे अचूक उत्तर देण्यासाठी सत्यापित ज्ञान स्रोतांमध्ये पुरेशी माहिती सापडली नाही. कृपया उद्धृत अधिकृत स्रोत पहा किंवा संबंधित सहकारी प्राधिकरणाशी संपर्क साधा.",
        "listening_text": "ऐकत आहे...",
        "processing_text": "प्रक्रिया करत आहे...",
        "report_title": "सहाय्यक AI - सहकारी अनुपालन अहवाल",
        "report_query": "वापरकर्ता प्रश्न",
        "report_answer": "AI उत्तर",
        "report_sources": "स्रोत",
        "report_date": "तारीख",
        "report_language": "भाषा",
        "suggested": [
            "PACS चे सदस्य होण्यासाठी कोणती कागदपत्रे आवश्यक आहेत?",
            "PMFBY म्हणजे काय?",
            "सहकारी तक्रार कशी दाखल करावी?",
            "सहकारी सदस्याचे हक्क काय आहेत?",
            "PACS द्वारे कोणत्या सेवा पुरवल्या जातात?"
        ]
    },
    "bn": {
        "code": "bn",
        "name": "Bengali",
        "nativeName": "বাংলা",
        "flag": "🇮🇳",
        "stt_code": "bn-IN",
        "tts_code": "bn-IN",
        "tts_lang": "bn-IN",
        "speechRecognition": "bn-IN",
        "ttsLanguage": "bn-IN",
        "bcp47": "bn-IN",
        "voice_names": ["Bengali", "bn-IN", "Bangla"],
        "instruction": "শুধু বাংলায় উত্তর দিন। পুনরুদ্ধার করা প্রমাণ ব্যবহার করে স্বাভাবিক বাংলায় উত্তর দিন।",
        "llm_instruction": "The user has selected Bengali (বাংলা). Answer ONLY in Bengali. Use retrieved knowledge as factual source. Do not answer in English. Preserve official names like PMFBY, PACS accurately.",
        "fallback_message": "এই প্রশ্নের সঠিক উত্তর দেওয়ার জন্য যাচাইকৃত জ্ঞান উৎসে পর্যাপ্ত তথ্য পাওয়া যায়নি। অনুগ্রহ করে উদ্ধৃত সরকারী উৎস দেখুন বা সংশ্লিষ্ট সমবায় কর্তৃপক্ষের সাথে যোগাযোগ করুন।",
        "listening_text": "শুনছি...",
        "processing_text": "প্রক্রিয়া করছি...",
        "report_title": "সহায়ক AI - সমবায় সম্মতি প্রতিবেদন",
        "report_query": "ব্যবহারকারীর প্রশ্ন",
        "report_answer": "AI উত্তর",
        "report_sources": "উৎস",
        "report_date": "তারিখ",
        "report_language": "ভাষা",
        "suggested": [
            "PACS-এর সদস্য হতে কী কী নথি প্রয়োজন?",
            "PMFBY কী?",
            "সমবায় অভিযোগ কীভাবে দায়ের করবেন?",
            "সমবায় সদস্যের অধিকার কী কী?",
            "PACS কী কী পরিষেবা প্রদান করে?"
        ]
    }
}

# Unicode ranges for script detection
SCRIPT_RANGES = {
    "ta": (0x0B80, 0x0BFF),
    "hi": (0x0900, 0x097F),
    "ml": (0x0D00, 0x0D7F),
    "te": (0x0C00, 0x0C7F),
    "kn": (0x0C80, 0x0CFF),
    "bn": (0x0980, 0x09FF),
    "mr": (0x0900, 0x097F),
}

LANGUAGE_MARKERS = {
    "ta": ["என்ன", "ஒரு", "சங்கத்தில்", "தேவை", "எவ்வாறு", "உரிமை"],
    "hi": ["क्या", "कैसे", "है", "के", "लिए", "दस्तावेज"],
    "ml": ["എന്ത്", "എങ്ങനെ", "ആണ്", "വേണം"],
    "te": ["ఏమిటి", "ఎలా", "కోసం", "అవసరం"],
    "kn": ["ಏನು", "ಹೇಗೆ", "ಬೇಕಾಗಿದೆ"],
    "mr": ["काय", "कसे", "आहे", "साठी"],
    "bn": ["কি", "কিভাবে", "প্রয়োজন"],
}

def detect_language_by_script(text: str) -> Optional[str]:
    if not text or not text.strip():
        return None
    script_counts = {lang: 0 for lang in SCRIPT_RANGES}
    for char in text:
        code = ord(char)
        for lang, (start, end) in SCRIPT_RANGES.items():
            if start <= code <= end:
                script_counts[lang] += 1
    devanagari_count = script_counts.get("hi", 0)
    if devanagari_count > 0:
        if "ळ" in text or "मराठी" in text:
            return "mr"
        if any(word in text for word in ["आहे", "होण्यासाठी", "म्हणजे"]):
            return "mr"
        return "hi"
    max_lang = None
    max_count = 0
    for lang, count in script_counts.items():
        if lang in ["hi", "mr"]:
            continue
        if count > max_count:
            max_count = count
            max_lang = lang
    if max_count > len(text) * 0.1:
        return max_lang
    return None

def detect_language(text: str, selected_language: str = "en") -> str:
    """
    Detect language BUT selected language has priority
    Priority: Manual selected > Auto detection
    If user explicitly selected a language (not en default), use it
    """
    # If selected language is explicitly non-English, it should have priority
    # But we still detect for logging, but we return selected if it's not en or if detection fails
    # For this function, we return detected, but caller should prioritize selected
    if not text or not text.strip():
        return selected_language
    
    script_lang = detect_language_by_script(text)
    if script_lang:
        return script_lang
    
    try:
        from langdetect import detect
        from langdetect.lang_detect_exception import LangDetectException
        try:
            detected = detect(text)
            mapping = {"ta": "ta", "hi": "hi", "ml": "ml", "te": "te", "kn": "kn", "mr": "mr", "bn": "bn", "en": "en"}
            if detected in mapping:
                if detected != "en" and len(text) < 20:
                    ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text) if text else 0
                    if ascii_ratio > 0.8:
                        return "en"
                return mapping[detected]
        except LangDetectException:
            pass
    except ImportError:
        pass
    
    for lang, markers in LANGUAGE_MARKERS.items():
        for marker in markers:
            if marker in text:
                return lang
    
    return selected_language if selected_language in LANGUAGE_CONFIG else "en"

def get_language_config(lang_code: str) -> Dict:
    return LANGUAGE_CONFIG.get(lang_code, LANGUAGE_CONFIG["en"])

def get_llm_instruction(lang_code: str) -> str:
    """Get LLM instruction for language enforcement"""
    config = get_language_config(lang_code)
    return config.get("llm_instruction", config.get("instruction", "Respond only in English."))

def classify_query_domain(question: str) -> str:
    """
    Classify query into 8 topics for better filtering
    Priority: CROP_INSURANCE > GRIEVANCE > COOPERATIVE_LAW (rights) > PACS_SERVICE > others
    """
    q_lower = question.lower()
    
    # CROP_INSURANCE - highest priority
    crop_keywords = ["pmfby", "crop insurance", "फसल बीमा", "பயிர் காப்பீடு", "crop loss", "premium", "claim", "bima", "insurance", "wbcis", "rwbcis", "फसल", "பயிர்", "വിള ഇൻഷുറൻസ്", "పంట బీమా", "ಬೆಳೆ ವಿಮೆ", "पीक विमा", "ফসল বিমা"]
    if any(k in q_lower for k in crop_keywords):
        return "CROP_INSURANCE"
    
    # GRIEVANCE
    grievance_keywords = ["grievance", "complaint", "शिकायत", "புகார்", "പരാതി", "cpgrams", "pgportal", "complain", "तक्रार", "অভিযোগ", "ഫയൽ ചെയ്യാം", "దాఖలు", "ಸಲ್ಲಿಸುವುದು", "दाखल", "দায়ের"]
    if any(k in q_lower for k in grievance_keywords):
        return "GRIEVANCE_REDDRESSAL"
    
    # COOPERATIVE_LAW - rights, act, law - should be checked BEFORE PACS because rights queries may contain cooperative words
    law_rights_keywords = [
        "rights", "right", "உரிமை", "உரிமைகள்", "अधिकार", "അവകാശ", "അവകാശങ്ങൾ", "హక్కులు", "హక్కు", "ಹಕ್ಕುಗಳು", "ಹಕ್ಕು", "हक्क", "অধিকার",
        "member rights", "cooperative member rights", "உறுப்பினர் உரிமை", "सदस्य अधिकार", "അംഗ അവകാശ", "సభ్యుని హక్కు", "ಸದಸ್ಯರ ಹಕ್ಕು", "सदस्य हक्क", "সদস্য অধিকার"
    ]
    if any(k in q_lower for k in law_rights_keywords):
        return "COOPERATIVE_LAW"
    
    law_keywords = ["act", "section", "law", "bye-law", "byelaw", "rule", "election", "board", "audit", "disqualification", "अधिनियम", "धारा", "சட்டம்", "നിയമം", "చట్టం", "ಕಾಯ್ದೆ", "कायदा", "আইন"]
    # Only classify as law if not explicitly about PACS membership docs
    if any(k in q_lower for k in law_keywords):
        # Check if it's really about law, not just PACS docs
        if not any(doc_word in q_lower for doc_word in ["document", "दस्तावेज", "രേഖകൾ", "పత్రాలు", "ದಾಖಲೆಗಳು", "कागदपत्रे", "নথি", "ஆவணங்கள்"]):
            return "COOPERATIVE_LAW"
    
    # PACS_SERVICE - multilingual keywords
    pacs_keywords = [
        "pacs", "primary agricultural credit", "membership", "kcc", "kisan credit", 
        "சேர", "दस्तावेज", "membership", "loan", "deposit", "சங்கத்தில்", "सदस्य",
        # Malayalam
        "അംഗമാകാൻ", "രേഖകൾ", "സഹകരണ", "സംഘത്തിൽ", "അംഗത്വം",
        # Telugu
        "సభ్యుడిగా", "పత్రాలు", "సహకార", "సభ్యత్వం",
        # Kannada
        "ಸದಸ್ಯರಾಗಲು", "ದಾಖಲೆಗಳು", "ಸಹಕಾರಿ", "ಸದಸ್ಯತ್ವ",
        # Marathi
        "सदस्य", "कागदपत्रे", "सहकारी",
        # Bengali
        "সদস্য", "নথি", "সমবায়", "সদস্যপদ",
        # Tamil additional
        "ஆவணங்கள்", "உறுப்பினராக",
        # Hindi additional
        "दस्तावेज़", "सदस्य", "सहकारी",
        # General
        "document", "required", "join"
    ]
    if any(k in q_lower for k in pacs_keywords):
        if "pmfby" not in q_lower and "insurance" not in q_lower and "बीमा" not in q_lower and "காப்பீடு" not in q_lower and "ഇൻഷുറൻസ്" not in q_lower and "బీమా" not in q_lower and "ವಿಮಾ" not in q_lower and "विमा" not in q_lower and "বিমা" not in q_lower:
            return "PACS_SERVICE"
    
    # GOVERNMENT_SCHEME
    scheme_keywords = ["scheme", "yojana", "योजना", "திட்டம்", "പദ്ധതി", "subsidy", "sahakar mit", "sahkar", "computerization", "grain storage", "csc", "myscheme", "पद्धति", "योजना"]
    if any(k in q_lower for k in scheme_keywords):
        return "GOVERNMENT_SCHEME"
    
    # FINANCIAL_LITERACY
    finance_keywords = ["financial literacy", "savings", "interest", "repayment", "credit score", "banking", "financial planning"]
    if any(k in q_lower for k in finance_keywords):
        return "FINANCIAL_LITERACY"
    
    # COOPERATIVE_GOVERNANCE
    governance_keywords = ["governance", "board", "committee", "meeting", "audit", "election", "general body", "managing committee"]
    if any(k in q_lower for k in governance_keywords):
        return "COOPERATIVE_GOVERNANCE"
    
    # Default - check if PACS related as fallback
    if "pacs" in q_lower:
        return "PACS_SERVICE"
    
    return "GENERAL_COOPERATIVE"

def get_fallback_message(lang_code: str) -> str:
    config = get_language_config(lang_code)
    return config["fallback_message"]

def get_report_labels(lang_code: str) -> Dict[str, str]:
    """Get report labels in selected language"""
    config = get_language_config(lang_code)
    return {
        "title": config.get("report_title", "SAHAYAK AI Report"),
        "query": config.get("report_query", "Query"),
        "answer": config.get("report_answer", "Answer"),
        "sources": config.get("report_sources", "Sources"),
        "date": config.get("report_date", "Date"),
        "language": config.get("report_language", "Language"),
    }

# ===== CRITICAL LANGUAGE LOCK FIX - STRICT VALIDATION =====

def get_strict_language_prompt(lang_code: str) -> str:
    """
    Create STRICT language prompt that LLM MUST obey.
    This is the SINGLE SOURCE OF TRUTH for response language.
    """
    config = get_language_config(lang_code)
    native_name = config.get("nativeName", lang_code)
    name = config.get("name", lang_code)
    
    # Language-specific strict instructions
    prompts = {
        "en": f"""You are Sahayak AI.

The user selected English.

Your response MUST be written entirely in English.

IMPORTANT:
- Answer ONLY in English.
- Do not answer in Tamil, Hindi, Malayalam, Telugu, Kannada, Marathi, Bengali.
- Do not switch languages.
- Do not choose another language based on the question.
- Do not choose another language based on the retrieved documents.

Use the retrieved evidence only for factual information.
Explain the information naturally and clearly in English.

The selected language is: English
Language code: en
This instruction has higher priority than detected language, source language, retrieved document language, previous response language, conversation language.""",

        "ta": f"""You are Sahayak AI.

The user selected Tamil (தமிழ்).

Your response MUST be written entirely in Tamil (தமிழ்).

CRITICAL RULES - HIGHEST PRIORITY:
- Answer ONLY in Tamil (தமிழ்).
- Do not answer in English.
- Do not answer in Hindi.
- Do not answer in Malayalam.
- Do not answer in Telugu, Kannada, Marathi, Bengali.
- Do not switch languages.
- Do not choose another language based on the question.
- Do not choose another language based on the retrieved documents.
- Do not choose another language based on the source documents.
- Even if retrieved documents are in English, you MUST answer in Tamil.

Use the retrieved evidence only for factual information.
Extract facts from English documents but explain naturally and clearly in Tamil.

Official names, law names, scheme names and abbreviations may remain in their official form when necessary (e.g., PMFBY, PACS, KCC) but explain them in Tamil.

The selected language is: Tamil (தமிழ்)
Language code: ta
Native name: தமிழ்

This instruction has higher priority than:
- detected language
- source language  
- retrieved document language
- previous response language
- conversation language

SELECTED LANGUAGE = RESPONSE LANGUAGE. User selected Tamil, so response MUST be Tamil.""",

        "hi": f"""You are Sahayak AI.

The user selected Hindi (हिन्दी).

Your response MUST be written entirely in Hindi (हिन्दी).

CRITICAL RULES - HIGHEST PRIORITY:
- Answer ONLY in Hindi.
- Do not answer in English.
- Do not answer in Tamil, Malayalam, etc.
- Do not switch languages.
- Even if retrieved documents are in English, you MUST answer in Hindi.

Use the retrieved evidence only for factual information.
Extract facts from English documents but explain naturally in Hindi.

Official names may remain in official form but explain in Hindi.

The selected language is: Hindi (हिन्दी)
Language code: hi

SELECTED LANGUAGE = RESPONSE LANGUAGE. User selected Hindi, so response MUST be Hindi.""",

        "ml": f"""You are Sahayak AI.

The user selected Malayalam (മലയാളം).

Your response MUST be written entirely in Malayalam (മലയാളം).

CRITICAL RULES:
- Answer ONLY in Malayalam.
- Do not answer in English.
- Even if retrieved documents are in English, you MUST answer in Malayalam.

Use retrieved evidence only for factual information.
Extract facts but explain in Malayalam.

Selected language: Malayalam (മലയാളം)
Language code: ml

SELECTED LANGUAGE = RESPONSE LANGUAGE. User selected Malayalam, so response MUST be Malayalam.""",

        "te": f"""You are Sahayak AI.

The user selected Telugu (తెలుగు).

Your response MUST be written entirely in Telugu (తెలుగు).

CRITICAL RULES:
- Answer ONLY in Telugu.
- Do not answer in English.
- Even if retrieved documents are in English, you MUST answer in Telugu.

Selected language: Telugu (తెలుగు)
Language code: te

SELECTED LANGUAGE = RESPONSE LANGUAGE. User selected Telugu, so response MUST be Telugu.""",

        "kn": f"""You are Sahayak AI.

The user selected Kannada (ಕನ್ನಡ).

Your response MUST be written entirely in Kannada (ಕನ್ನಡ).

CRITICAL RULES:
- Answer ONLY in Kannada.
- Do not answer in English.
- Even if retrieved documents are in English, you MUST answer in Kannada.

Selected language: Kannada (ಕನ್ನಡ)
Language code: kn

SELECTED LANGUAGE = RESPONSE LANGUAGE. User selected Kannada, so response MUST be Kannada.""",

        "mr": f"""You are Sahayak AI.

The user selected Marathi (मराठी).

Your response MUST be written entirely in Marathi (मराठी).

CRITICAL RULES:
- Answer ONLY in Marathi.
- Do not answer in English.

Selected language: Marathi (मराठी)
Language code: mr

SELECTED LANGUAGE = RESPONSE LANGUAGE. User selected Marathi, so response MUST be Marathi.""",

        "bn": f"""You are Sahayak AI.

The user selected Bengali (বাংলা).

Your response MUST be written entirely in Bengali (বাংলা).

CRITICAL RULES:
- Answer ONLY in Bengali.
- Do not answer in English.

Selected language: Bengali (বাংলা)
Language code: bn

SELECTED LANGUAGE = RESPONSE LANGUAGE. User selected Bengali, so response MUST be Bengali."""
    }
    
    return prompts.get(lang_code, prompts["en"])

def is_response_in_selected_language(response: str, selected_language: str) -> tuple:
    """
    Validate if response is in selected language.
    Returns (is_valid, detected_language, confidence)
    """
    if not response or not response.strip():
        return False, "unknown", 0.0
    
    # Count characters by script
    script_counts = {lang: 0 for lang in SCRIPT_RANGES}
    total_chars = 0
    
    for char in response:
        if char.strip() and not char.isdigit() and char not in ".,;:!?()[]{}'\"-•\n\r\t ":
            total_chars += 1
            code = ord(char)
            for lang, (start, end) in SCRIPT_RANGES.items():
                if start <= code <= end:
                    script_counts[lang] += 1
    
    # For English, check if predominantly ASCII and no other script
    if selected_language == "en":
        # English should be mostly ASCII and not contain other scripts significantly
        non_ascii_indic = sum(script_counts.values())
        # If contains Indic scripts, it's not English
        if non_ascii_indic > len(response) * 0.1:
            # Detect which Indic language
            max_lang = max(script_counts, key=script_counts.get)
            return False, max_lang, non_ascii_indic / len(response) if len(response) > 0 else 0
        return True, "en", 1.0
    
    # For non-English languages, check if contains expected script
    expected_script_count = script_counts.get(selected_language, 0)
    
    # Special handling for mr which shares Devanagari with hi
    if selected_language == "mr":
        devanagari_count = script_counts.get("hi", 0) + script_counts.get("mr", 0)
        # If has Devanagari, consider valid for mr (since mr uses Devanagari)
        # Check for Marathi-specific markers
        if devanagari_count > total_chars * 0.1 or total_chars == 0:
            # Additional check: if contains Marathi markers, it's mr, else could be hi but still Devanagari
            # For strictness, if selected is mr and has Devanagari, it's valid
            return True, "mr", devanagari_count / max(total_chars, 1)
        # If no Devanagari at all, it's likely English
        ascii_count = sum(1 for c in response if ord(c) < 128 and c.strip())
        if ascii_count > total_chars * 0.7:
            return False, "en", ascii_count / max(total_chars, 1)
        return False, "en", 0.0
    
    if selected_language == "hi":
        devanagari_count = script_counts.get("hi", 0) + script_counts.get("mr", 0)
        if devanagari_count > total_chars * 0.1:
            return True, "hi", devanagari_count / max(total_chars, 1)
        ascii_count = sum(1 for c in response if ord(c) < 128 and c.strip())
        if ascii_count > total_chars * 0.7:
            return False, "en", ascii_count / max(total_chars, 1)
        return False, "en", 0.0
    
    # For other languages with distinct scripts
    if expected_script_count > total_chars * 0.15:  # At least 15% should be in expected script
        return True, selected_language, expected_script_count / max(total_chars, 1)
    
    # Check if response is predominantly English (ASCII)
    ascii_count = sum(1 for c in response if ord(c) < 128 and c.strip() and c not in ".,;:!?()[]{}'\"-•")
    # If >70% ASCII and expected script is <15%, it's likely English when it should be Indic
    if ascii_count > total_chars * 0.7 and selected_language != "en":
        return False, "en", ascii_count / max(total_chars, 1)
    
    # If we have some of expected script but not enough, still consider invalid if mostly English
    if selected_language != "en" and expected_script_count == 0:
        return False, "en", 0.0
    
    return True, selected_language, expected_script_count / max(total_chars, 1)

def get_language_badge(lang_code: str) -> str:
    """Get language badge for debugging and user clarity"""
    config = get_language_config(lang_code)
    native = config.get("nativeName", lang_code)
    flag = config.get("flag", "🌐")
    return f"{flag} {native}"

def get_fallback_error_message(lang_code: str) -> str:
    """Get error message in selected language when generation fails"""
    messages = {
        "en": "The response could not be generated in the selected language. Please try again.",
        "ta": "தேர்ந்தெடுக்கப்பட்ட மொழியில் பதிலை உருவாக்க முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
        "hi": "चयनित भाषा में प्रतिक्रिया उत्पन्न नहीं की जा सकी। कृपया पुनः प्रयास करें।",
        "ml": "തിരഞ്ഞെടുത്ത ഭാഷയിൽ പ്രതികരണം സൃഷ്ടിക്കാൻ കഴിഞ്ഞില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക.",
        "te": "ఎంచుకున్న భాషలో ప్రతిస్పందనను రూపొందించలేకపోయింది. దయచేసి మళ్లీ ప్రయత్నించండి.",
        "kn": "ಆಯ್ಕೆಮಾಡಿದ ಭಾಷೆಯಲ್ಲಿ ಪ್ರತಿಕ್ರಿಯೆಯನ್ನು ರಚಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
        "mr": "निवडलेल्या भाषेत प्रतिसाद तयार करता आला नाही. कृपया पुन्हा प्रयत्न करा.",
        "bn": "নির্বাচিত ভাষায় প্রতিক্রিয়া তৈরি করা যায়নি। অনুগ্রহ করে আবার চেষ্টা করুন।"
    }
    return messages.get(lang_code, messages["en"])
