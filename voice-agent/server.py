"""
VaniSetu — Real-Time Voice Server (Phase 3)
Zero-Cost Voice AI Pipeline:
  - Browser Web Audio UI (Option A zero-friction dev testbed)
  - faster-whisper (local CPU STT, 0ms network latency)
  - OpenRouter Gemma/Nemotron (free tier LLM with multi-model fallback)
  - edge-tts (free neural Hindi TTS, in-memory audio streaming)
  - Platform & Rec Engine bridge (:3001 & :8000)

Usage:
    .venv\\Scripts\\python.exe server.py
    Open http://localhost:7860
"""

import sys
import os
import io
import time
import json
import base64
import uuid
import tempfile
import asyncio
import re
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import edge_tts
from faster_whisper import WhisperModel

from conversation_states import CallState, Stage, Profile
import agent
import api_bridge

# ── Configuration ─────────────────────────────────────────────────────────────
PORT = int(os.getenv("VOICE_SERVER_PORT", 7860))
TTS_VOICE = os.getenv("TTS_VOICE", "hi-IN-SwaraNeural")
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "small")

app = FastAPI(title="VaniSetu Voice Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load local STT Model once at startup ──────────────────────────────────────
print(f"Loading local STT model ({WHISPER_MODEL_NAME})...")
_STT_MODEL = WhisperModel(WHISPER_MODEL_NAME, device="cpu", compute_type="int8")
print(f"STT model loaded successfully.")

# Active call states: call_id -> CallState
_ACTIVE_CALLS: dict[str, CallState] = {}


# ── Audio Helper Functions ───────────────────────────────────────────────────

def transcribe_audio_bytes(audio_bytes: bytes, filename_hint: str = "audio.webm") -> str:
    """Transcribe audio bytes using local faster-whisper on CPU."""
    if not audio_bytes or len(audio_bytes) < 100:
        return ""

    suffix = Path(filename_hint).suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = _STT_MODEL.transcribe(
            tmp_path,
            language="hi",
            beam_size=3,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400),
        )
        text = "".join(s.text for s in segments).strip()
        return text
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


async def synthesize_speech(text: str, voice: str = TTS_VOICE) -> bytes:
    """Synthesize Hindi speech into MP3 bytes in memory."""
    if not text:
        return b""
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data


# ── Conversation Turn Processor ───────────────────────────────────────────────

async def process_call_turn(state: CallState, user_text: str) -> dict:
    """
    Executes one turn of conversation:
      1. LLM agent response & state machine transition
      2. Profile extraction
      3. Check for recommendation trigger
      4. Synthesize spoken Hindi audio
    """
    start_time = time.time()

    # 0. Auto-advance from Greeting to Identity if caller already spoke
    if state.stage == Stage.GREETING and user_text and not user_text.startswith("("):
        state.stage = Stage.IDENTITY

    # 1. Pre-extract fields from user text
    if user_text and not user_text.startswith("("):
        agent.apply_extraction(state, None, user_text=user_text)

    # 2. Advance to recommendation stage if profile is complete
    if state.ready_for_recommendation() and state.stage in (Stage.EDUCATION, Stage.PREFERENCES):
        state.stage = Stage.RECOMMEND

    # 3. If at recommendation stage, fetch recommendations once
    if state.stage == Stage.RECOMMEND and not state.recommendation:
        b_id = await api_bridge.register_beneficiary(state)
        rec_data = await api_bridge.fetch_recommendations(b_id, state)
        state.recommendation = rec_data

    # 4. Get response (LLM with seamless Hindi dialogue fallback)
    raw_reply = await agent.get_response(state, user_text or "(call started)")
    spoken = agent.clean_spoken_text(raw_reply)

    # 5. Update conversation history
    if user_text:
        state.history.append({"role": "user", "content": user_text})
    state.history.append({"role": "assistant", "content": raw_reply})

    # 6. Extract structured profile data from LLM JSON only (if returned)
    data = agent.extract_json(raw_reply)
    if data:
        agent.apply_extraction(state, data, user_text="")

    # Auto-advance from Greeting to Identity after opening turn
    if state.stage == Stage.GREETING:
        state.stage = Stage.IDENTITY

    # If call was confirmed, advance to END and log call
    if state.stage == Stage.CONFIRM:
        state.stage = Stage.END
        asyncio.create_task(api_bridge.log_call(state))

    # 5. Synthesize TTS audio for the spoken portion
    audio_bytes = await synthesize_speech(spoken)
    audio_b64 = base64.b64encode(audio_bytes).decode("ascii") if audio_bytes else ""

    elapsed = round(time.time() - start_time, 2)

    return {
        "call_id": state.call_id,
        "stage": state.stage.value,
        "user_text": user_text,
        "agent_text": spoken,
        "audio_b64": audio_b64,
        "profile": state.profile.__dict__,
        "ready_for_rec": state.ready_for_recommendation(),
        "recommendation": state.recommendation,
        "elapsed_seconds": elapsed,
    }


# ── REST API Endpoints ────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    backend_status = await api_bridge.check_health()
    return {
        "service": "VaniSetu Voice Agent Server",
        "status": "healthy",
        "llm_backend": agent.backend_name(),
        "stT_model": WHISPER_MODEL_NAME,
        "tts_voice": TTS_VOICE,
        "bridge": backend_status,
    }


@app.post("/api/call/start")
async def start_call():
    """Initializes a new call session and returns the opening Hindi greeting."""
    call_id = str(uuid.uuid4())
    state = CallState(call_id=call_id)
    _ACTIVE_CALLS[call_id] = state

    result = await process_call_turn(state, "(call started)")
    return JSONResponse(result)


@app.post("/api/call/voice-turn")
async def voice_turn(
    call_id: str = Form(...),
    audio: UploadFile = File(...),
):
    """Processes an audio chunk from the user's microphone."""
    state = _ACTIVE_CALLS.get(call_id)
    if not state:
        state = CallState(call_id=call_id)
        _ACTIVE_CALLS[call_id] = state

    audio_bytes = await audio.read()
    user_text = transcribe_audio_bytes(audio_bytes, audio.filename or "audio.webm")

    if not user_text:
        user_text = "(audio unclear / silence)"

    result = await process_call_turn(state, user_text)
    return JSONResponse(result)


@app.post("/api/call/text-turn")
async def text_turn(payload: dict):
    """Processes text turn (for testing without microphone)."""
    call_id = payload.get("call_id") or str(uuid.uuid4())
    user_text = payload.get("text", "").strip()

    state = _ACTIVE_CALLS.get(call_id)
    if not state:
        state = CallState(call_id=call_id)
        _ACTIVE_CALLS[call_id] = state

    result = await process_call_turn(state, user_text)
    return JSONResponse(result)


# ── WebSocket Real-Time Interface ─────────────────────────────────────────────

@app.websocket("/ws/call")
async def websocket_call(websocket: WebSocket):
    await websocket.accept()
    call_id = str(uuid.uuid4())
    state = CallState(call_id=call_id)
    _ACTIVE_CALLS[call_id] = state

    # Send opening greeting immediately on connection
    greeting_result = await process_call_turn(state, "(call started)")
    await websocket.send_json(greeting_result)

    try:
        while True:
            msg = await websocket.receive()
            if "bytes" in msg and msg["bytes"]:
                # Audio chunk from microphone
                audio_bytes = msg["bytes"]
                user_text = transcribe_audio_bytes(audio_bytes)
                if not user_text:
                    user_text = "(silence)"
                res = await process_call_turn(state, user_text)
                await websocket.send_json(res)
            elif "text" in msg and msg["text"]:
                data = json.loads(msg["text"])
                action = data.get("action")
                if action == "text_turn":
                    user_text = data.get("text", "").strip()
                    res = await process_call_turn(state, user_text)
                    await websocket.send_json(res)
                elif action == "end_call":
                    await api_bridge.log_call(state)
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await api_bridge.log_call(state)
        _ACTIVE_CALLS.pop(call_id, None)


# ── Interactive HTML5 Voice Client UI ────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return HTMLResponse(content=_HTML_PAGE)


_HTML_PAGE = """<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VaniSetu — PM-AJAY Voice AI Testbed</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: rgba(22, 29, 47, 0.7);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #f97316;
      --primary-glow: rgba(249, 115, 22, 0.35);
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.25);
      --success: #10b981;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg);
      background-image: 
        radial-gradient(at 0% 0%, rgba(249, 115, 22, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(56, 189, 248, 0.1) 0px, transparent 50%);
      color: var(--text);
      font-family: 'Outfit', 'Noto Sans Devanagari', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    header {
      padding: 1.25rem 2rem;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(11, 15, 25, 0.8);
      backdrop-filter: blur(12px);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .brand-logo {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, var(--primary), #ea580c);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.25rem;
      color: white;
      box-shadow: 0 0 20px var(--primary-glow);
    }

    .brand-title {
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }

    .brand-badge {
      font-size: 0.75rem;
      padding: 0.2rem 0.6rem;
      background: rgba(249, 115, 22, 0.15);
      border: 1px solid rgba(249, 115, 22, 0.3);
      border-radius: 9999px;
      color: var(--primary);
      font-weight: 600;
    }

    .status-badge {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.85rem;
      padding: 0.4rem 0.8rem;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 9999px;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
    }

    main {
      flex: 1;
      padding: 2rem;
      max-width: 1300px;
      margin: 0 auto;
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 380px;
      gap: 2rem;
    }

    .voice-console {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 1.5rem;
      backdrop-filter: blur(16px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }

    /* Stage Stepper */
    .stepper {
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: relative;
    }

    .step-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.35rem;
      position: relative;
      z-index: 2;
    }

    .step-circle {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #1e293b;
      border: 2px solid #334155;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8rem;
      font-weight: 600;
      transition: all 0.3s ease;
    }

    .step-item.active .step-circle {
      background: var(--primary);
      border-color: var(--primary);
      box-shadow: 0 0 16px var(--primary-glow);
    }

    .step-item.done .step-circle {
      background: var(--success);
      border-color: var(--success);
    }

    .step-label {
      font-size: 0.75rem;
      color: var(--text-muted);
      font-weight: 500;
    }

    .step-item.active .step-label {
      color: var(--text);
      font-weight: 600;
    }

    /* Voice Interactive Hub */
    .voice-hub {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2.5rem 1.5rem;
      position: relative;
      overflow: hidden;
    }

    .pulse-ring {
      width: 140px;
      height: 140px;
      border-radius: 50%;
      background: radial-gradient(circle, var(--primary-glow) 0%, transparent 70%);
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      opacity: 0;
      pointer-events: none;
      transition: all 0.3s ease;
    }

    .pulse-ring.active {
      opacity: 1;
      animation: pulse 1.8s infinite;
    }

    @keyframes pulse {
      0% { transform: translate(-50%, -50%) scale(0.9); opacity: 0.8; }
      50% { transform: translate(-50%, -50%) scale(1.4); opacity: 0.2; }
      100% { transform: translate(-50%, -50%) scale(1.6); opacity: 0; }
    }

    .mic-button {
      width: 90px;
      height: 90px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--primary), #ea580c);
      border: 3px solid rgba(255, 255, 255, 0.2);
      color: white;
      font-size: 2rem;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 10px 25px var(--primary-glow);
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      z-index: 5;
    }

    .mic-button:hover {
      transform: scale(1.05);
      box-shadow: 0 15px 35px var(--primary-glow);
    }

    .mic-button:active, .mic-button.recording {
      transform: scale(0.95);
      background: #dc2626;
      box-shadow: 0 0 30px rgba(220, 38, 38, 0.6);
    }

    .voice-status-text {
      margin-top: 1.5rem;
      font-size: 1rem;
      font-weight: 500;
      color: var(--text);
    }

    .voice-hint {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }

    /* Transcript Box */
    .transcript-box {
      height: 280px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      padding-right: 0.5rem;
    }

    .msg {
      display: flex;
      flex-direction: column;
      max-width: 80%;
      padding: 0.85rem 1.15rem;
      border-radius: 14px;
      font-size: 0.95rem;
      line-height: 1.5;
    }

    .msg-user {
      align-self: flex-end;
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: #e0f2fe;
    }

    .msg-agent {
      align-self: flex-start;
      background: rgba(249, 115, 22, 0.12);
      border: 1px solid rgba(249, 115, 22, 0.25);
      color: #ffedd5;
    }

    .msg-sender {
      font-size: 0.75rem;
      font-weight: 600;
      margin-bottom: 0.25rem;
      opacity: 0.8;
    }

    /* Text fallback input */
    .text-input-bar {
      display: flex;
      gap: 0.75rem;
      margin-top: 1rem;
    }

    .text-input {
      flex: 1;
      padding: 0.75rem 1rem;
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      color: white;
      font-size: 0.95rem;
      outline: none;
    }

    .text-input:focus {
      border-color: var(--primary);
    }

    .btn-send {
      padding: 0.75rem 1.25rem;
      background: var(--primary);
      border: none;
      border-radius: 10px;
      color: white;
      font-weight: 600;
      cursor: pointer;
    }

    /* Sidebar cards */
    .sidebar {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .field-row {
      display: flex;
      justify-content: space-between;
      padding: 0.6rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      font-size: 0.9rem;
    }

    .field-label { color: var(--text-muted); }
    .field-val { font-weight: 600; color: var(--text); }

    .rec-card {
      border: 1px solid rgba(16, 185, 129, 0.3);
      background: rgba(16, 185, 129, 0.08);
      border-radius: 12px;
      padding: 1rem;
      margin-top: 0.75rem;
    }

    .rec-title {
      font-weight: 700;
      color: #34d399;
      font-size: 1rem;
      margin-bottom: 0.4rem;
    }

    .rec-badge {
      display: inline-block;
      font-size: 0.75rem;
      background: rgba(16, 185, 129, 0.2);
      color: #10b981;
      padding: 0.2rem 0.5rem;
      border-radius: 6px;
      margin-bottom: 0.5rem;
      font-weight: 600;
    }

    .rec-desc {
      font-size: 0.85rem;
      color: #d1fae5;
      line-height: 1.4;
    }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-logo">V</div>
      <div>
        <div class="brand-title">VaniSetu Voice Agent</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">PM-AJAY GIA SC Beneficiary Calling System</div>
      </div>
      <span class="brand-badge">$0 Cost Architecture</span>
    </div>
    <div class="status-badge">
      <div class="status-dot"></div>
      <span id="backendStatus">Local AI Ready (Whisper + OpenRouter + edge-tts)</span>
    </div>
  </header>

  <main>
    <section class="voice-console">
      
      <!-- Stage Stepper -->
      <div class="card">
        <div class="stepper" id="stepper">
          <div class="step-item active" data-stage="greeting">
            <div class="step-circle">1</div>
            <div class="step-label">नमस्ते</div>
          </div>
          <div class="step-item" data-stage="identity">
            <div class="step-circle">2</div>
            <div class="step-label">पहचान</div>
          </div>
          <div class="step-item" data-stage="livelihood">
            <div class="step-circle">3</div>
            <div class="step-label">काम / हुनर</div>
          </div>
          <div class="step-item" data-stage="education">
            <div class="step-circle">4</div>
            <div class="step-label">शिक्षा</div>
          </div>
          <div class="step-item" data-stage="recommendation">
            <div class="step-circle">5</div>
            <div class="step-label">ट्रेनिंग ऑफर</div>
          </div>
          <div class="step-item" data-stage="confirmation">
            <div class="step-circle">6</div>
            <div class="step-label">रजिस्ट्रेशन</div>
          </div>
        </div>
      </div>

      <!-- Live Voice Hub -->
      <div class="card voice-hub">
        <div class="pulse-ring" id="pulseRing"></div>
        <button class="mic-button" id="micBtn" title="बोलने के लिए दबाएं / Push to Speak">
          🎙️
        </button>
        <div class="voice-status-text" id="statusText">कॉल शुरू करने के लिए माइक दबाएं</div>
        <div class="voice-hint" id="statusHint">Push to talk — speak in Hindi or English</div>

        <!-- Audio Output element -->
        <audio id="audioPlayer" autoplay></audio>
      </div>

      <!-- Transcript Box -->
      <div class="card">
        <h3 style="font-size: 0.95rem; margin-bottom: 0.75rem; color: var(--text-muted);">लाइव बातचीत (Transcript)</h3>
        <div class="transcript-box" id="transcriptBox">
          <div class="msg msg-agent">
            <span class="msg-sender">PM-AJAY सहायक 🤖</span>
            <span>नमस्ते! मैं PM-AJAY सहायक हूँ। माइक दबाकर बोलना शुरू करें या नीचे लिखकर जवाब दें।</span>
          </div>
        </div>

        <!-- Text input fallback -->
        <div class="text-input-bar">
          <input type="text" id="textInput" class="text-input" placeholder="या यहाँ लिखकर भेजें (उदा: मेरा नाम रमेश है, रांची से हूँ)..." />
          <button class="btn-send" id="btnSend">भेजें</button>
        </div>
      </div>

    </section>

    <!-- Sidebar Profile & Recommendation -->
    <aside class="sidebar">

      <div class="card">
        <h3 style="font-size: 1rem; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between;">
          <span>आवेदक प्रोफ़ाइल (Live)</span>
          <span id="readyBadge" style="font-size: 0.75rem; color: var(--text-muted);">अपूर्ण</span>
        </h3>
        <div class="field-row">
          <span class="field-label">नाम:</span>
          <span class="field-val" id="profName">—</span>
        </div>
        <div class="field-row">
          <span class="field-label">उम्र:</span>
          <span class="field-val" id="profAge">—</span>
        </div>
        <div class="field-row">
          <span class="field-label">जिला:</span>
          <span class="field-val" id="profDistrict">—</span>
        </div>
        <div class="field-row">
          <span class="field-label">काम / पेशा:</span>
          <span class="field-val" id="profOccupation">—</span>
        </div>
        <div class="field-row">
          <span class="field-label">हुनर (Skills):</span>
          <span class="field-val" id="profSkills">—</span>
        </div>
        <div class="field-row">
          <span class="field-label">शिक्षा:</span>
          <span class="field-val" id="profEducation">—</span>
        </div>
        <div class="field-row">
          <span class="field-label">जाति वर्ग:</span>
          <span class="field-val" style="color: #38bdf8;">अनुसूचित जाति (SC)</span>
        </div>
      </div>

      <!-- Recommendation Card -->
      <div class="card" id="recSection" style="display: none;">
        <h3 style="font-size: 1rem; color: #34d399;">🎯 ट्रेनिंग सिफारिश (NSQF Match)</h3>
        <div class="rec-card" id="recCard">
          <div class="rec-title" id="recProgram">कारपेंटर विशेष प्रशिक्षण</div>
          <span class="rec-badge" id="recBadge">NSQF Level 4 • 100% Free PM-AJAY</span>
          <p class="rec-desc" id="recDesc">विवरण लोड हो रहा है...</p>
        </div>
      </div>

    </aside>
  </main>

  <script>
    let callId = null;
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;

    const micBtn = document.getElementById('micBtn');
    const pulseRing = document.getElementById('pulseRing');
    const statusText = document.getElementById('statusText');
    const statusHint = document.getElementById('statusHint');
    const transcriptBox = document.getElementById('transcriptBox');
    const textInput = document.getElementById('textInput');
    const btnSend = document.getElementById('btnSend');
    const audioPlayer = document.getElementById('audioPlayer');

    // Profile DOM elements
    const profName = document.getElementById('profName');
    const profAge = document.getElementById('profAge');
    const profDistrict = document.getElementById('profDistrict');
    const profOccupation = document.getElementById('profOccupation');
    const profSkills = document.getElementById('profSkills');
    const profEducation = document.getElementById('profEducation');
    const readyBadge = document.getElementById('readyBadge');

    // Recommendation DOM
    const recSection = document.getElementById('recSection');
    const recProgram = document.getElementById('recProgram');
    const recBadge = document.getElementById('recBadge');
    const recDesc = document.getElementById('recDesc');

    // ── Mic & Audio Recording ────────────────────────────────────────────────
    async function initMic() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
          const blob = new Blob(audioChunks, { type: 'audio/webm' });
          audioChunks = [];
          await sendAudioBlob(blob);
        };
        return true;
      } catch (err) {
        console.error("Mic access error:", err);
        statusText.textContent = "माइक्रोफ़ोन की अनुमति दें या नीचे टाइप करें";
        statusHint.textContent = "Microphone access blocked. Use text input below.";
        return false;
      }
    }

    async function toggleRecording() {
      if (!mediaRecorder) {
        const ok = await initMic();
        if (!ok) return;
      }

      if (!isRecording) {
        audioChunks = [];
        mediaRecorder.start();
        isRecording = true;
        micBtn.classList.add('recording');
        pulseRing.classList.add('active');
        statusText.textContent = "सुन रहा हूँ... बोलना खत्म करने पर दोबारा दबाएं";
        statusHint.textContent = "Listening... tap mic again when done";
      } else {
        mediaRecorder.stop();
        isRecording = false;
        micBtn.classList.remove('recording');
        pulseRing.classList.remove('active');
        statusText.textContent = "आवाज़ समझी जा रही है (Whisper AI)...";
        statusHint.textContent = "Processing speech locally...";
      }
    }

    micBtn.addEventListener('click', toggleRecording);

    // ── API Communication ───────────────────────────────────────────────────
    async function sendAudioBlob(blob) {
      const formData = new FormData();
      if (!callId) callId = "call-" + Date.now();
      formData.append("call_id", callId);
      formData.append("audio", blob, "voice.webm");

      try {
        const res = await fetch("/api/call/voice-turn", { method: "POST", body: formData });
        const data = await res.json();
        handleServerTurn(data);
      } catch (err) {
        console.error("Voice turn error:", err);
        statusText.textContent = "सर्वर से संपर्क नहीं हुआ";
      }
    }

    async function sendTextTurn(text) {
      if (!text.trim()) return;
      if (!callId) callId = "call-" + Date.now();

      appendTranscript("user", text);
      textInput.value = "";
      statusText.textContent = "सहायक सोच रहा है...";

      try {
        const res = await fetch("/api/call/text-turn", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ call_id: callId, text: text })
        });
        const data = await res.json();
        handleServerTurn(data);
      } catch (err) {
        console.error("Text turn error:", err);
        statusText.textContent = "सर्वर से संपर्क नहीं हुआ";
      }
    }

    btnSend.addEventListener('click', () => sendTextTurn(textInput.value));
    textInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') sendTextTurn(textInput.value);
    });

    // ── Handle Server Turn Response ─────────────────────────────────────────
    function handleServerTurn(data) {
      if (data.call_id) callId = data.call_id;

      if (data.user_text && data.user_text !== "(call started)" && !data.user_text.startsWith("(")) {
        appendTranscript("user", data.user_text);
      }

      if (data.agent_text) {
        appendTranscript("agent", data.agent_text);
      }

      // Play synthesized audio
      if (data.audio_b64) {
        audioPlayer.src = "data:audio/mp3;base64," + data.audio_b64;
        audioPlayer.play().catch(e => console.log("Autoplay notice:", e));
      }

      // Update state stepper
      updateStepper(data.stage);

      // Update profile
      if (data.profile) {
        const p = data.profile;
        if (p.name) profName.textContent = p.name;
        if (p.age) profAge.textContent = p.age + " वर्ष";
        if (p.district) profDistrict.textContent = p.district;
        if (p.occupation) profOccupation.textContent = p.occupation;
        if (p.skills && p.skills.length > 0) profSkills.textContent = p.skills.join(", ");
        if (p.education) profEducation.textContent = p.education.replace('_', ' ').toUpperCase();

        if (data.ready_for_rec) {
          readyBadge.textContent = "✅ तैयार";
          readyBadge.style.color = "var(--success)";
        }
      }

      // Update Recommendation Card if present
      if (data.recommendation && data.recommendation.recommendations && data.recommendation.recommendations.length > 0) {
        const rec = data.recommendation.recommendations[0];
        recSection.style.display = "block";
        recProgram.textContent = rec.program_name;
        recBadge.textContent = `NSQF Level ${rec.nsqf_level} • ${rec.duration_hours}h • 100% Free`;
        recDesc.textContent = rec.explanation_text;
      }

      statusText.textContent = "माइक दबाकर बोलें";
      statusHint.textContent = `Turn completed in ${data.elapsed_seconds || 1.5}s`;
    }

    function appendTranscript(role, text) {
      const div = document.createElement('div');
      div.className = `msg msg-${role}`;
      div.innerHTML = `
        <span class="msg-sender">${role === 'user' ? 'आप (Caller) 👤' : 'PM-AJAY सहायक 🤖'}</span>
        <span>${text}</span>
      `;
      transcriptBox.appendChild(div);
      transcriptBox.scrollTop = transcriptBox.scrollHeight;
    }

    function updateStepper(stage) {
      const stages = ["greeting", "identity", "livelihood", "education", "recommendation", "confirmation"];
      const currentIdx = stages.indexOf(stage);

      document.querySelectorAll('.step-item').forEach((el, idx) => {
        el.classList.remove('active', 'done');
        if (idx < currentIdx) {
          el.classList.add('done');
        } else if (idx === currentIdx) {
          el.classList.add('active');
        }
      });
    }

    // Auto-init call greeting on page load
    window.addEventListener('load', async () => {
      try {
        const res = await fetch("/api/call/start", { method: "POST" });
        const data = await res.json();
        handleServerTurn(data);
      } catch (e) {
        console.log("Startup init:", e);
      }
    });
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    print("=" * 64)
    print(f"  VaniSetu Voice Server starting on http://localhost:{PORT}")
    print(f"  STT: faster-whisper ({WHISPER_MODEL_NAME}) on CPU")
    print(f"  TTS: edge-tts ({TTS_VOICE})")
    print(f"  LLM: {agent.backend_name()}")
    print("=" * 64)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
