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

_FALLBACK_RESPONSES = {
    Stage.GREETING: "नमस्ते! मैं PM-AJAY Sahayak हूँ। आपका नाम क्या है?",
    Stage.IDENTITY: "क्षमा करें, थोड़ी तकनीकी दिक्कत आई। आपका जिला कौन सा है?",
    Stage.LIVELIHOOD: "आप अभी क्या काम करते हैं?",
    Stage.EDUCATION: "आपने कौन सी कक्षा तक पढ़ाई की?",
    Stage.RECOMMEND: "आपके लिए एक बढ़िया training program है। क्या आप details जानना चाहते हैं?",
}


# ── Core LLM call ─────────────────────────────────────────────────────────────

async def get_response(state: CallState, user_text: str) -> str:
    """Get LLM response for the current stage. Returns spoken Hindi text."""
    system = _PROMPTS.get(state.stage, _PROMPTS[Stage.GREETING])
    messages = [{"role": "system", "content": system}]
    messages.extend(state.recent_history(6))
    messages.append({"role": "user", "content": user_text})

    is_openrouter = "openrouter" in str(_CLIENT.base_url)
    kwargs = {
        "model": _MODEL,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 800,  # ample space for reasoning + output
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
        if content:
            return content.strip()
    except Exception as e:
        backend = "OpenRouter" if is_openrouter else "Ollama"
        print(f"  [LLM/{backend}] {type(e).__name__}: {e}")

    return _FALLBACK_RESPONSES.get(state.stage, "माफ़ करें, दोबारा बोलें।")


# ── Text Cleaning & JSON extraction ───────────────────────────────────────────

def clean_spoken_text(text: str) -> str:
    """Strip <think>...</think> and ```json...``` from text before sending to TTS or displaying."""
    t = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    t = re.sub(r"```(?:json)?.*?```", "", t, flags=re.DOTALL)
    t = re.sub(r"^.*?<\/think>", "", t, flags=re.DOTALL)
    return t.strip()


def extract_json(text: str) -> dict | None:
    """Pull the real populated JSON object from an LLM response, ignoring schema templates and think blocks."""
    # First strip any <think> ... </think> block
    clean_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    clean_text = re.sub(r"^.*?<\/think>", "", clean_text, flags=re.DOTALL).strip()
    target = clean_text if clean_text else text
    candidates = []

    # 1. Check all markdown fenced code blocks
    for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", target, re.DOTALL):
        try:
            candidates.append(json.loads(m.group(1)))
        except json.JSONDecodeError:
            pass

    # 2. If no fenced blocks, find balanced { ... } blocks
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

    # Prefer candidate with real data (no "..." placeholder strings)
    valid = [c for c in candidates if isinstance(c, dict) and not any(v == "..." for v in c.values())]
    return valid[-1] if valid else (candidates[-1] if candidates else None)


def apply_extraction(state: CallState, data: dict | None, user_text: str = ""):
    """Update CallState.profile from extracted JSON and user input fallbacks."""
    p = state.profile
    data = data or {}

    if state.stage == Stage.IDENTITY:
        if data.get("name"):     p.name     = str(data["name"])
        if data.get("district"): p.district = str(data["district"])
        if data.get("state"):    p.state    = str(data["state"])
        if data.get("age"):      p.age      = int(data["age"]) if str(data["age"]).isdigit() else None
        
        # User text heuristics if LLM missed fields
        if user_text and not p.name:
            m = re.search(r"naam\s+([A-Za-z\u0900-\u097F]+(?:\s+[A-Za-z\u0900-\u097F]+)?)", user_text, re.IGNORECASE)
            if m:
                p.name = m.group(1).strip()
        if user_text and not p.district:
            for d in ["Ranchi", "Dhanbad", "Patna", "Delhi", "Lucknow", "Jaipur", "Bhopal", "Mumbai", "Pune"]:
                if d.lower() in user_text.lower():
                    p.district = d
                    break
        if state.identity_done():
            state.next_stage()

    elif state.stage == Stage.LIVELIHOOD:
        if data.get("occupation"): p.occupation = str(data["occupation"])
        if data.get("skills"):     p.skills     = list(data["skills"]) if isinstance(data["skills"], list) else [str(data["skills"])]
        elif data.get("occupation") and not p.skills:
            p.skills = [p.occupation]
        if data.get("years"):      p.years_exp  = int(data["years"]) if str(data["years"]).isdigit() else None
        if data.get("sector"):     p.sector     = str(data["sector"])

        # Fallback keywords if LLM missed occupation
        if user_text and not p.occupation:
            for kw, occ in [("furniture", "Carpenter"), ("carpentr", "Carpenter"), ("lakdi", "Carpenter"),
                            ("kapde", "Tailor"), ("tailor", "Tailor"), ("silai", "Tailor"),
                            ("khet", "Farmer"), ("kisan", "Farmer"), ("mobile", "Mobile Technician")]:
                if kw in user_text.lower():
                    p.occupation = occ
                    if not p.skills:
                        p.skills = [occ]
                    break
        if state.livelihood_done():
            state.next_stage()

    elif state.stage == Stage.EDUCATION:
        if data.get("education"):  p.education = str(data["education"])
        if user_text and not p.education:
            for kw, edu in [("10th", "10th_pass"), ("दसवीं", "10th_pass"), ("12th", "12th_pass"),
                            ("8th", "8th_pass"), ("iti", "iti"), ("diploma", "diploma"), ("graduate", "graduate")]:
                if kw in user_text.lower():
                    p.education = edu
                    break
        if p.education:
            state.next_stage()


def backend_name() -> str:
    """Returns which LLM backend is active."""
    return "OpenRouter" if "openrouter" in str(_CLIENT.base_url) else f"Ollama ({_MODEL})"

