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
            "google/gemma-3-27b-it:free",
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

    try:
        resp = await _CLIENT.chat.completions.create(
            model=_MODEL,
            messages=messages,
            temperature=0.6,
            max_tokens=280,  # short = less TTS latency
        )
        return resp.choices[0].message.content or _FALLBACK_RESPONSES.get(state.stage, "")
    except Exception as e:
        backend = "OpenRouter" if "openrouter" in str(_CLIENT.base_url) else "Ollama"
        print(f"  [LLM/{backend}] {type(e).__name__}: {e}")
        return _FALLBACK_RESPONSES.get(state.stage, "माफ़ करें, दोबारा बोलें।")


# ── JSON extraction ───────────────────────────────────────────────────────────

def extract_json(text: str) -> dict | None:
    """Pull the first JSON object from an LLM response."""
    # Try fenced block first, then raw object
    for pattern in (r"```json\s*(\{.*?\})\s*```", r"(\{[^{}]+\})"):
        m = re.search(pattern, text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    return None


def apply_extraction(state: CallState, data: dict):
    """Update CallState.profile from extracted JSON. Advances stage when complete."""
    p = state.profile

    if state.stage == Stage.IDENTITY:
        if data.get("name"):     p.name     = data["name"]
        if data.get("district"): p.district = data["district"]
        if data.get("state"):    p.state    = data["state"]
        if data.get("age"):      p.age      = data["age"]
        if state.identity_done():
            state.next_stage()

    elif state.stage == Stage.LIVELIHOOD:
        if data.get("occupation"): p.occupation = data["occupation"]
        if data.get("skills"):     p.skills     = data["skills"]
        if data.get("years"):      p.years_exp  = data["years"]
        if data.get("sector"):     p.sector     = data["sector"]
        if state.livelihood_done():
            state.next_stage()

    elif state.stage == Stage.EDUCATION:
        if data.get("education"):  p.education = data["education"]
        if p.education:
            state.next_stage()


def backend_name() -> str:
    """Returns which LLM backend is active."""
    return "OpenRouter" if "openrouter" in str(_CLIENT.base_url) else f"Ollama ({_MODEL})"
