"""
VaniSetu — LLM Conversation Agent
Zero-cost LLM strategy:
  1. OpenRouter :free models (GitHub signup, no card)
  2. Ollama local fallback (winget install Ollama.Ollama, no account)
"""

import json
import os
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv
from conversation_states import CallState, Stage

load_dotenv()

# ── Client setup — tries OpenRouter, falls back to Ollama ────────────────────

def _make_client() -> tuple[AsyncOpenAI, str]:
    """Returns (client, model_id). Prefers OpenRouter, falls back to Ollama."""
    or_key = os.getenv("OPENROUTER_API_KEY", "")
    if or_key and not or_key.startswith("sk-or-v1-REPLACE"):
        return (
            AsyncOpenAI(
                api_key=or_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/harshhujare/Vaani",
                    "X-Title": "VaniSetu PM-AJAY Voice Agent",
                },
            ),
            "openrouter/free",
        )

    # Ollama fallback — 100% local, no account, no internet at inference time
    return (
        AsyncOpenAI(
            api_key="ollama",          # required but unused
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/v1",
        ),
        os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
    )


_CLIENT, _MODEL = _make_client()


# ── System prompts per stage ──────────────────────────────────────────────────

_PROMPTS: dict[Stage, str] = {

    Stage.GREETING: """\
तुम PM-AJAY सहायक हो — एक सरकारी AI जो PM-AJAY GIA योजना के तहत अनुसूचित जाति के लोगों को
निशुल्क कौशल प्रशिक्षण कार्यक्रम खोजने में मदद करता है।

कॉलर का गर्मजोशी से स्वागत करो। खुद को "PM-AJAY Sahayak" के रूप में परिचित कराओ।
उनसे उनका नाम पूछो। 2 वाक्यों से ज्यादा नहीं। हिंदी में बोलो।""",

    Stage.IDENTITY: """\
तुम PM-AJAY Sahayak हो। तुम्हें कॉलर से ये जानकारी चाहिए: नाम, उम्र (approximate), जिला।

एक बार में एक ही सवाल पूछो। जो पहले से बता दिया है उसे दोबारा मत पूछो।
हिंदी में बोलो, सरल और स्पष्ट।

हर जवाब के अंत में, जो डेटा मिला है उसे इस JSON में निकालो (बाकी response के बाद):
```json
{"name": "...", "age": null, "district": "...", "state": "..."}
```
अगर कोई field नहीं मिली तो null रखो।""",

    Stage.LIVELIHOOD: """\
तुम PM-AJAY Sahayak हो। अब कॉलर के काम और हुनर के बारे में जानो:
- वो अभी क्या काम करते हैं?
- कितने साल से?
- उनके खास हुनर (skills) क्या हैं?

एक बार में एक सवाल। हिंदी में बोलो।

उनके जवाब से skills को structured format में निकालो:
- "furniture banata hoon" → skills: ["Carpentry", "Furniture Making"]
- "kapde silta hoon" → skills: ["Tailoring", "Stitching"]
- "khet mein kaam karta hoon" → skills: ["Agriculture", "Farming"]
- "mobile repair" → skills: ["Mobile Repair", "Electronics"]
- "rasoi ka kaam" → skills: ["Cooking", "Food Processing"]

हर जवाब के बाद:
```json
{"occupation": "...", "years": null, "sector": "...", "skills": ["...", "..."]}
```""",

    Stage.EDUCATION: """\
तुम PM-AJAY Sahayak हो। कॉलर की शिक्षा के बारे में पूछो। सम्मान से पूछो।

इन में से एक map करो:
below_8th | 8th_pass | 10th_pass | 12th_pass | iti | diploma | graduate | post_graduate

हर जवाब के बाद:
```json
{"education": "10th_pass"}
```""",

    Stage.RECOMMEND: """\
तुम PM-AJAY Sahayak हो। तुम्हारे पास कॉलर के लिए training recommendation है।
उन्हें सरल, उत्साहजनक हिंदी में बताओ।

नियम:
- program का नाम, duration, और कि यह बिल्कुल MUFT है (सरकारी योजना) — ये ज़रूर बताओ
- certificate मिलेगा — ये ज़रूर बताओ
- job placement या salary की गारंटी मत दो
- explanation_text को base बनाओ, नया मत बनाओ
- अंत में पूछो: "क्या आप इस training में register करना चाहते हैं?" """,
}

# ── Contextual Dialogue Fallback (when LLM is rate-limited / offline) ────────

_HINDI_NUMS = {
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5,
    "छह": 6, "छे": 6, "सात": 7, "साथ": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15,
    "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19, "बीस": 20,
    "इक्कीस": 21, "बाईस": 22, "तेईस": 23, "चौबीस": 24, "पच्चीस": 25, "पच्छीस": 25, "पच्छी": 25,
    "छब्बीस": 26, "सत्ताईस": 27, "अट्ठाईस": 28, "उनतीस": 29, "तीस": 30,
    "पैंतीस": 35, "चालीस": 40, "पचास": 50,
}

def parse_hindi_num(text: str) -> int | None:
    """Parses digits or Hindi phonetic number words into integers."""
    m = re.search(r"(\d+)", text)
    if m:
        return int(m.group(1))
    for word, val in _HINDI_NUMS.items():
        if re.search(rf"\b{word}\b|{word}", text):
            return val
    return None

def build_contextual_response(state: CallState, user_text: str = "") -> str:
    """
    Generates a natural, warm, context-aware Hindi dialogue response.
    Guarantees the voice call NEVER gets stuck or repeats questions.
    """
    p = state.profile

    if state.stage == Stage.GREETING:
        return "नमस्ते! मैं PM-AJAY सहायक हूँ, सरकारी कौशल विकास योजना से। आपका शुभ नाम क्या है?"

    elif state.stage == Stage.IDENTITY:
        if p.name and not p.district:
            return f"नमस्ते {p.name} जी! आपका जिला और राज्य कौन सा है?"
        elif p.district and not p.name:
            return f"धन्यवाद! आपका जिला {p.district} दर्ज कर लिया गया है। कृपया अपना नाम बताएं।"
        elif p.name and p.district:
            return f"धन्यवाद {p.name} जी! आप {p.district} से हैं। अब कृपया बताएं कि आप अभी क्या काम या व्यवसाय करते हैं और आपको कितने साल का अनुभव है?"
        return "नमस्ते! कृपया अपना नाम और जिला बताएं।"

    elif state.stage == Stage.LIVELIHOOD:
        if p.occupation or p.skills:
            occ = p.occupation or (p.skills[0] if p.skills else "काम")
            return f"समझ गया {p.name or ''} जी, आप {occ} का काम करते हैं। आपने कौन सी कक्षा तक पढ़ाई की है? (जैसे 8वीं, 10वीं, 12वीं या आईटीआई)"
        return f"{p.name or ''} जी, आप अभी कौन सा काम या हुनर का काम करते हैं और आपको कितने साल का अनुभव है?"

    elif state.stage in (Stage.EDUCATION, Stage.PREFERENCES):
        if p.education:
            return f"बहुत अच्छा {p.name or ''} जी। आपकी जानकारी के आधार पर PM-AJAY योजना के तहत आपके लिए सबसे उपयुक्त मुफ्त ट्रेनिंग प्रोग्राम तैयार किया जा रहा है..."
        return f"{p.name or ''} जी, आपने किस कक्षा तक पढ़ाई की है? जैसे 8वीं, 10वीं, 12वीं पास या आईटीआई?"

    elif state.stage == Stage.RECOMMEND:
        rec = {}
        if state.recommendation and state.recommendation.get("recommendations"):
            rec = state.recommendation["recommendations"][0]
        occ_clean = p.occupation or "कौशल विकास"
        if len(occ_clean) > 25:
            occ_clean = "कौशल विकास"
        prog = rec.get("program_name") or f"{occ_clean} विशेष प्रशिक्षण (NSQF Level 4)"
        prov = rec.get("provider_name") or f"PM-AJAY कौशल केंद्र, {p.district or 'आपके जिले'}"
        dur = rec.get("duration_hours") or 240
        return (
            f"खुशखबरी {p.name or ''} जी! आपके अनुभव और योग्यता के अनुसार {prog} का सरकारी कार्यक्रम {prov} में उपलब्ध है। "
            f"यह {dur} घंटे का 100% मुफ्त सरकारी प्रशिक्षण है जिसमें NSQF सर्टिफिकेट मिलेगा। "
            f"क्या आप इसमें अपना पंजीकरण (रजिस्ट्रेशन) कराना चाहते हैं?"
        )

    elif state.stage in (Stage.CONFIRM, Stage.END):
        return (
            f"बधाई हो {p.name or ''} जी! आपका नाम PM-AJAY कौशल योजना में सफलतापूर्वक दर्ज कर लिया गया है। "
            f"हमारे {p.district or ''} केंद्र से अधिकारी आपको जल्द कॉल करेंगे। PM-AJAY से जुड़ने के लिए धन्यवाद!"
        )

    return "जी, मैं आपकी बात सुन रहा हूँ। कृपया आगे बताएं।"


# ── Core LLM call ─────────────────────────────────────────────────────────────

async def get_response(state: CallState, user_text: str) -> str:
    """Get LLM response for current stage, or seamless contextual dialogue fallback."""
    system = _PROMPTS.get(state.stage, _PROMPTS[Stage.GREETING])
    messages = [{"role": "system", "content": system}]
    messages.extend(state.recent_history(6))
    messages.append({"role": "user", "content": user_text})

    is_openrouter = "openrouter" in str(_CLIENT.base_url)
    kwargs = {
        "model": _MODEL,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 800,
    }
    if is_openrouter:
        kwargs["extra_body"] = {
            "models": [
                "google/gemma-4-26b-a4b-it:free",
                "google/gemma-4-31b-it:free",
                "nvidia/nemotron-3-super-120b-a12b:free",
            ]
        }

    try:
        resp = await _CLIENT.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        content = msg.content or getattr(msg, "reasoning", None)
        if content and len(content.strip()) > 5:
            return content.strip()
    except Exception as e:
        backend = "OpenRouter" if is_openrouter else "Ollama"
        print(f"  [LLM/{backend}] {type(e).__name__}: {e}")

    # Fallback to intelligent local Hindi dialogue manager
    return build_contextual_response(state, user_text)


# ── Text Cleaning & JSON extraction ───────────────────────────────────────────

def clean_spoken_text(text: str) -> str:
    """Strip <think>...</think> and ```json...``` from text before sending to TTS or displaying."""
    t = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    t = re.sub(r"```(?:json)?.*?```", "", t, flags=re.DOTALL)
    t = re.sub(r"^.*?<\/think>", "", t, flags=re.DOTALL)
    return t.strip()


def extract_json(text: str) -> dict | None:
    """Pull the real populated JSON object from an LLM response, ignoring schema templates and think blocks."""
    clean_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    clean_text = re.sub(r"^.*?<\/think>", "", clean_text, flags=re.DOTALL).strip()
    target = clean_text if clean_text else text
    candidates = []

    for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", target, re.DOTALL):
        try:
            candidates.append(json.loads(m.group(1)))
        except json.JSONDecodeError:
            pass

    if not candidates:
        start = 0
        while True:
            s_idx = target.find("{", start)
            if s_idx == -1:
                break
            depth = 0
            for i in range(s_idx, len(target)):
                if target[i] == "{":
                    depth += 1
                elif target[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            candidates.append(json.loads(target[s_idx : i + 1]))
                        except json.JSONDecodeError:
                            pass
                        start = i + 1
                        break
            else:
                break

    valid = [c for c in candidates if isinstance(c, dict) and not any(v == "..." for v in c.values())]
    return valid[-1] if valid else (candidates[-1] if candidates else None)


def apply_extraction(state: CallState, data: dict | None, user_text: str = ""):
    """Update CallState.profile from extracted JSON and robust Hindi/English text parsing."""
    p = state.profile
    data = data or {}

    if state.stage in (Stage.GREETING, Stage.IDENTITY):
        if data.get("name"):     p.name     = str(data["name"])
        if data.get("district"): p.district = str(data["district"])
        if data.get("state"):    p.state    = str(data["state"])
        if data.get("age"):      p.age      = int(data["age"]) if str(data["age"]).isdigit() else None

        # ── 1. Name parsing (Hindi & English) ─────────────────────────────────
        if user_text and not p.name:
            # Pattern: मेरा नाम साहिल है / mera naam sahil hai / naam sahil / my name is sahil
            m = re.search(r"(?:मेरा\s+)?नाम\s+(?:है\s+)?([A-Za-z\u0900-\u097F]+)", user_text, re.IGNORECASE)
            if not m:
                m = re.search(r"(?:naam\s+(?:hai\s+)?|my\s+name\s+is\s+)([A-Za-z\u0900-\u097F]+)", user_text, re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                if cand not in ("है", "hai", "ka", "mera", "मेरा"):
                    p.name = cand
            elif len(user_text.split()) <= 2 and not p.district:
                # Single word like "साहिल" or "Sahil"
                cand = re.sub(r"[^\w\u0900-\u097F]", "", user_text).strip()
                if cand and cand not in ("नमस्ते", "namaste", "hello", "hi", "हाँ", "नहीं"):
                    p.name = cand

        # ── 2. District parsing (Hindi & English) ─────────────────────────────
        if user_text and not p.district:
            # Pattern: मेरा जिला सांगली है / jila sangli / district sangli / sangli jila
            m = re.search(r"(?:जिला|district|jila)\s+(?:है\s+)?([A-Za-z\u0900-\u097F]+)", user_text, re.IGNORECASE)
            if not m:
                m = re.search(r"([A-Za-z\u0900-\u097F]+)\s+(?:जिला|district|jila)", user_text, re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                if cand not in ("है", "hai", "mera", "मेरा", "ka", "mein", "में"):
                    p.district = cand
            elif p.name and len(user_text.split()) <= 3:
                # Name is already known, user answered with their district
                cand = re.sub(r"[^\w\u0900-\u097F]", "", user_text).strip()
                if cand and cand not in ("हाँ", "नहीं", "yes", "no", "namaste", "नमस्ते", "है", "hai"):
                    p.district = cand

            # Known districts check
            for d in [
                "Sangli", "सांगली", "Pune", "पुणे", "Mumbai", "मुंबई", "Nagpur", "नागपुर", "Solapur", "सोलापुर",
                "Kolhapur", "कोल्हापुर", "Nashik", "नासिक", "Thane", "ठाणे",
                "Ranchi", "रांची", "Dhanbad", "धनबाद", "Patna", "पटना", "Delhi", "दिल्ली",
                "Lucknow", "लखनऊ", "Jaipur", "जयपुर", "Bhopal", "भोपाल"
            ]:
                if d.lower() in user_text.lower():
                    p.district = d
                    break

        # ── 3. State parsing ──────────────────────────────────────────────────
        if user_text and not p.state:
            for st_kw, st_name in [
                ("महाराष्ट्र", "Maharashtra"), ("महराश्ट्र", "Maharashtra"), ("माराश्ट्र", "Maharashtra"), ("maharashtra", "Maharashtra"),
                ("झारखंड", "Jharkhand"), ("jharkhand", "Jharkhand"),
                ("बिहार", "Bihar"), ("bihar", "Bihar"),
                ("दिल्ली", "Delhi"), ("delhi", "Delhi"),
                ("उत्तर प्रदेश", "Uttar Pradesh"), ("up", "Uttar Pradesh"),
                ("राजस्थान", "Rajasthan"), ("मध्य प्रदेश", "Madhya Pradesh")
            ]:
                if st_kw in user_text.lower():
                    p.state = st_name
                    break

        # ── 4. Age parsing ────────────────────────────────────────────────────
        if user_text and not p.age:
            m = re.search(r"(\d+|पच्चीस|पच्छीस|पच्छी|बीस|तीस|चालीस|अठारह|उन्नीस)\s*(?:saal|साल|years|वर्ष|umar|उम्र|की\s+उम्र|उंग्र)", user_text, re.IGNORECASE)
            if m:
                p.age = parse_hindi_num(m.group(1))

        if state.identity_done():
            state.stage = Stage.LIVELIHOOD

    elif state.stage == Stage.LIVELIHOOD:
        if data.get("occupation"): p.occupation = str(data["occupation"])
        if data.get("skills"):     p.skills     = list(data["skills"]) if isinstance(data["skills"], list) else [str(data["skills"])]
        elif data.get("occupation") and not p.skills:
            p.skills = [p.occupation]
        if data.get("years"):      p.years_exp  = int(data["years"]) if str(data["years"]).isdigit() else None
        if data.get("sector"):     p.sector     = str(data["sector"])

        # Occupation keywords (Hindi & English)
        if user_text and not p.occupation:
            for kw, occ in [
                ("दरजी", "Tailor (दर्जी)"), ("दर्जी", "Tailor (दर्जी)"), ("सिलाई", "Tailor (दर्जी)"),
                ("सिलता", "Tailor (दर्जी)"), ("सिल्ता", "Tailor (दर्जी)"), ("सिलने", "Tailor (दर्जी)"),
                ("कपड़े", "Tailor (दर्जी)"), ("कप्रे", "Tailor (दर्जी)"), ("कपड़ा", "Tailor (दर्जी)"),
                ("tailor", "Tailor (दर्जी)"), ("silai", "Tailor (दर्जी)"), ("kapde", "Tailor (दर्जी)"),
                ("बढ़ई", "Carpenter (बढ़ई)"), ("बढई", "Carpenter (बढ़ई)"), ("फर्नीचर", "Carpenter (बढ़ई)"),
                ("लकड़ी", "Carpenter (बढ़ई)"), ("lakdi", "Carpenter (बढ़ई)"), ("furniture", "Carpenter (बढ़ई)"), ("carpentr", "Carpenter (बढ़ई)"),
                ("वेल्डिंग", "Welder (वेल्डर)"), ("वेल्डर", "Welder (वेल्डर)"), ("welder", "Welder (वेल्डर)"), ("welding", "Welder (वेल्डर)"),
                ("बिजली", "Electrician (बिजली मिस्त्री)"), ("इलेक्ट्रीशियन", "Electrician (बिजली मिस्त्री)"), ("electric", "Electrician (बिजली मिस्त्री)"),
                ("प्लंबर", "Plumber"), ("प्लम्बर", "Plumber"), ("नल", "Plumber"), ("plumber", "Plumber"),
                ("ड्राइवर", "Driver"), ("ड्राईवर", "Driver"), ("गाड़ी", "Driver"), ("driver", "Driver"),
                ("मिस्त्री", "Mason (राजमिस्त्री)"), ("राजमिस्त्री", "Mason (राजमिस्त्री)"), ("मजदूरी", "Construction Worker"),
                ("खेती", "Farmer (किसान)"), ("किसान", "Farmer (किसान)"), ("khet", "Farmer (किसान)"), ("kisan", "Farmer (किसान)"),
                ("मोबाइल", "Mobile Technician"), ("mobile", "Mobile Technician"),
                ("खाना", "Cook"), ("रसोई", "Cook"), ("cooking", "Cook")
            ]:
                if kw in user_text.lower():
                    p.occupation = occ
                    if not p.skills:
                        p.skills = [occ]
                    break

        if user_text and not p.years_exp:
            m = re.search(r"(\d+|एक|दो|तीन|चार|पांच|पाँच|छह|छे|सात|साथ|आठ|नौ|दस)\s*(?:saal|साल|years|वर्ष)", user_text, re.IGNORECASE)
            if m:
                p.years_exp = parse_hindi_num(m.group(1))

        if state.livelihood_done():
            state.stage = Stage.EDUCATION

    elif state.stage in (Stage.EDUCATION, Stage.PREFERENCES):
        if data.get("education"):  p.education = str(data["education"])
        if user_text and not p.education:
            for kw, edu in [
                ("12th", "12th_pass"), ("बारहवीं", "12th_pass"), ("बारहवी", "12th_pass"), ("बारवी", "12th_pass"), ("बारवीं", "12th_pass"), ("12 वीं", "12th_pass"),
                ("10th", "10th_pass"), ("दसवीं", "10th_pass"), ("दसवी", "10th_pass"), ("10 वीं", "10th_pass"), ("मैट्रिक", "10th_pass"),
                ("8th", "8th_pass"), ("आठवीं", "8th_pass"), ("आठवी", "8th_pass"), ("8 वीं", "8th_pass"),
                ("iti", "iti"), ("आईटीआई", "iti"), ("आई टी आई", "iti"),
                ("diploma", "diploma"), ("डिप्लोमा", "diploma"),
                ("graduate", "graduate"), ("ग्रेजुएट", "graduate"), ("बीए", "graduate"), ("ba", "graduate"), ("bcom", "graduate"),
                ("below_8th", "below_8th"), ("अनपढ़", "below_8th"), ("स्कूल नहीं", "below_8th")
            ]:
                if kw in user_text.lower():
                    p.education = edu
                    break

        # Also extract age if mentioned here (e.g. "मेरी उम्र 25 साल है, और मैं 12वीं पास हूँ")
        if user_text and not p.age:
            m = re.search(r"(\d+|पच्चीस|पच्छीस|पच्छी|बीस|तीस|चालीस|अठारह|उन्नीस)\s*(?:saal|साल|years|वर्ष|umar|उम्र|की\s+उम्र|उंग्र)", user_text, re.IGNORECASE)
            if m:
                p.age = parse_hindi_num(m.group(1))

        if p.education:
            state.stage = Stage.RECOMMEND

    elif state.stage == Stage.RECOMMEND:
        # Check confirmation (हाँ, हा, जी, yes, etc.)
        if user_text:
            text_clean = user_text.strip().lower()
            affirmations = [
                "हाँ", "हां", "हा", "ह", "जी", "जी हाँ", "जी हां", "हाँ जी", "हां जी",
                "yes", "ha", "haan", "theek", "theek hai", "karo", "kar do",
                "register", "पंजीकरण", "पंजीयन", "कराना है", "करना है", "चाहता हूँ", "चाहती हूँ",
                "ज़रूर", "जरूर", "ok", "done", "confirm"
            ]
            if any(text_clean == aff or aff in text_clean.split() for aff in affirmations) or text_clean in ["हा", "हाँ", "हां", "जी"]:
                state.stage = Stage.CONFIRM

    elif state.stage == Stage.CONFIRM:
        state.stage = Stage.END


def backend_name() -> str:
    """Returns which LLM backend is active."""
    return "OpenRouter" if "openrouter" in str(_CLIENT.base_url) else f"Ollama ({_MODEL})"

