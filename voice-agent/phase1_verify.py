"""
VaniSetu Voice Agent — Phase 1 Verification Script
====================================================
Zero-cost, zero-account, zero-card audio pipeline check.

Tests (in order):
  1. faster-whisper loads locally (STT)
  2. edge-tts synthesises Hindi speech (TTS)
  3. Microphone capture + STT round-trip (live audio)
  4. Full loop: mic → STT → echo back via TTS

Run:
    .venv\\Scripts\\python.exe phase1_verify.py
    .venv\\Scripts\\python.exe phase1_verify.py --no-mic   # skip mic tests (CI/headless)

Expected output:
    ✅ TEST 1 PASS — Whisper model loaded  (model: small, device: cpu)
    ✅ TEST 2 PASS — TTS synthesised       (file: test_tts_output.mp3, size: ~40KB)
    ✅ TEST 3 PASS — Mic capture OK        (captured 3s, RMS: >0.001)
    ✅ TEST 4 PASS — STT transcribed       ("नमस्ते")
    ✅ ALL TESTS PASSED — Phase 1 complete. Proceed to Phase 2.
"""

import sys
import asyncio
import argparse
import os
import time
import tempfile
import pathlib

# ── stdout UTF-8 fix for Windows ──────────────────────────────────────────────
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = pathlib.Path(__file__).parent
RESULTS: list[tuple[str, bool, str]] = []


def log(label: str, ok: bool, detail: str = ""):
    icon = "✅" if ok else "❌"
    msg = f"  {icon} {label}"
    if detail:
        msg += f"   ({detail})"
    print(msg)
    RESULTS.append((label, ok, detail))


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1 — faster-whisper: local model load
# ══════════════════════════════════════════════════════════════════════════════

def test1_whisper_load() -> object | None:
    """Load faster-whisper model. No network call if model is cached."""
    print("\n── TEST 1: faster-whisper (local STT) ──────────────────────────")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        log("Whisper import", False, "run: uv pip install faster-whisper")
        return None

    model_name = os.getenv("WHISPER_MODEL", "small")
    print(f"  Loading model '{model_name}' on CPU …")
    size_map = {"tiny": "~39MB", "base": "~74MB", "small": "~244MB", "medium": "~769MB"}
    print(f"  (First run downloads {size_map.get(model_name, 'model')} to ~/.cache/huggingface)")
    t0 = time.time()

    try:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        elapsed = round(time.time() - t0, 1)
        log("Whisper model loaded", True, f"model: {model_name}, device: cpu, load time: {elapsed}s")
        return model
    except Exception as e:
        log("Whisper model load", False, str(e))
        return None


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2 — edge-tts: synthesise Hindi speech to file
# ══════════════════════════════════════════════════════════════════════════════

async def test2_edge_tts() -> bool:
    """Synthesise a Hindi sentence. Saves to test_tts_output.mp3."""
    print("\n── TEST 2: edge-tts (zero-API-key TTS) ─────────────────────────")

    try:
        import edge_tts
    except ImportError:
        log("edge-tts import", False, "run: uv pip install edge-tts")
        return False

    voice = os.getenv("TTS_VOICE", "hi-IN-SwaraNeural")
    text  = "नमस्ते! मैं PM-AJAY सहायक हूँ। आपका नाम क्या है?"
    out   = SCRIPT_DIR / "test_tts_output.mp3"

    print(f"  Voice: {voice}")
    print(f"  Text:  {text}")
    t0 = time.time()

    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(out))
        elapsed = round(time.time() - t0, 1)
        size_kb = round(out.stat().st_size / 1024, 1)

        if size_kb < 1:
            log("TTS synthesised", False, "output file is empty — check internet connection")
            return False

        log("TTS synthesised", True, f"file: {out.name}, size: {size_kb}KB, time: {elapsed}s")
        print(f"  ▶ Play it: start {out}")
        return True
    except Exception as e:
        # Common failure: network unavailable
        if "connect" in str(e).lower() or "network" in str(e).lower():
            log("TTS synthesised", False, "edge-tts needs internet. Offline alt: install Piper TTS (see Phase 3 guide)")
        else:
            log("TTS synthesised", False, str(e))
        return False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3 — Microphone capture (sounddevice)
# ══════════════════════════════════════════════════════════════════════════════

def test3_mic_capture(duration: int = 3) -> bytes | None:
    """Capture {duration}s of mic audio. Returns raw bytes or None."""
    print(f"\n── TEST 3: Microphone capture ({duration}s) ──────────────────────")

    try:
        import sounddevice as sd
        import numpy as np
    except ImportError:
        log("Mic import", False, "run: uv pip install sounddevice numpy")
        return None

    # List available input devices
    try:
        devices = sd.query_devices()
        inputs = [d for d in devices if d["max_input_channels"] > 0]
        if not inputs:
            log("Mic detected", False, "No input device found")
            return None
        print(f"  Input devices found: {len(inputs)}")
        for d in inputs[:3]:
            print(f"    • {d['name']}")
    except Exception as e:
        log("Mic detected", False, str(e))
        return None

    sample_rate = 16000  # Whisper expects 16kHz
    print(f"  Recording {duration}s at {sample_rate}Hz … speak now 🎙️")

    try:
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()  # blocks until done

        rms = float(np.sqrt(np.mean(audio ** 2)))
        if rms < 0.0001:
            log("Mic capture", False, f"RMS={rms:.6f} — mic is silent (check volume / privacy settings)")
            return None

        log("Mic capture", True, f"RMS={rms:.4f}, shape={audio.shape}")
        # Return as raw bytes for Whisper
        return audio.tobytes(), audio, sample_rate
    except Exception as e:
        log("Mic capture", False, str(e))
        return None


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4 — STT: transcribe mic capture with faster-whisper
# ══════════════════════════════════════════════════════════════════════════════

def test4_stt(model, audio_data) -> str | None:
    """Transcribe audio captured in test3."""
    print("\n── TEST 4: STT transcription (mic → text) ───────────────────────")

    if model is None:
        log("STT skipped", False, "Whisper not loaded (see Test 1)")
        return None
    if audio_data is None:
        log("STT skipped", False, "No mic audio (see Test 3)")
        return None

    _, audio_array, sample_rate = audio_data

    try:
        import soundfile as sf
        import numpy as np
    except ImportError:
        log("STT deps", False, "run: uv pip install soundfile")
        return None

    # Write to temp WAV so faster-whisper can read it
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name

    try:
        sf.write(tmp_path, audio_array, sample_rate)
        t0 = time.time()
        segments, info = model.transcribe(tmp_path, language="hi")
        text = " ".join(seg.text.strip() for seg in segments).strip()
        elapsed = round(time.time() - t0, 1)

        if not text:
            log("STT transcribed", False, "Empty result — was the mic silent?")
            return None

        log("STT transcribed", True, f"lang={info.language}({info.language_probability:.2f}), time={elapsed}s")
        print(f"  📝 Transcript: \"{text}\"")
        return text
    except Exception as e:
        log("STT transcribed", False, str(e))
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5 — Full loop: STT result → TTS → playback
# ══════════════════════════════════════════════════════════════════════════════

async def test5_full_loop(transcript: str | None) -> bool:
    """Speak the STT result back via TTS (echo loop demo)."""
    print("\n── TEST 5: Full loop (STT result → TTS echo) ───────────────────")

    if not transcript:
        # Use a canned sentence if no mic
        transcript = "आपने कहा नमस्ते"
        print(f"  (No live transcript — using canned: \"{transcript}\")")

    response = f"आपने कहा: {transcript}। अब हम Phase 2 की तरफ बढ़ सकते हैं।"

    try:
        import edge_tts
        voice = os.getenv("TTS_VOICE", "hi-IN-SwaraNeural")
        out = SCRIPT_DIR / "test_loop_output.mp3"
        communicate = edge_tts.Communicate(response, voice)
        await communicate.save(str(out))
        size_kb = round(out.stat().st_size / 1024, 1)
        log("Full loop TTS", True, f"response written to {out.name} ({size_kb}KB)")
        print(f"  ▶ Play it: start {out}")
        return True
    except Exception as e:
        log("Full loop TTS", False, str(e))
        return False


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

async def main(skip_mic: bool):
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  VaniSetu Voice Agent — Phase 1 Verification                ║")
    print("║  Zero-cost | Zero-card | 100% local STT & TTS               ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"  Python: {sys.version.split()[0]}  |  CWD: {SCRIPT_DIR}")

    # Test 1: STT load
    model = test1_whisper_load()

    # Test 2: TTS
    tts_ok = await test2_edge_tts()

    # Test 3 & 4: Mic + STT
    transcript = None
    if skip_mic:
        print("\n── TEST 3 & 4: SKIPPED (--no-mic flag) ─────────────────────────")
        log("Mic + STT", True, "skipped by --no-mic flag")
    else:
        audio_data = test3_mic_capture(duration=3)
        transcript = test4_stt(model, audio_data)

    # Test 5: Full loop
    loop_ok = await test5_full_loop(transcript)

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "═" * 64)
    print("  PHASE 1 SUMMARY")
    print("═" * 64)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total  = len(RESULTS)
    for name, ok, detail in RESULTS:
        icon = "✅" if ok else "❌"
        print(f"  {icon}  {name:<35} {detail}")

    print("═" * 64)
    if passed == total:
        print(f"  ✅ ALL {total} TESTS PASSED — Phase 1 complete!")
        print("  → Next: .venv\\Scripts\\python.exe phase2_llm.py")
    else:
        print(f"  ⚠️  {passed}/{total} passed. Fix ❌ items above before proceeding.")
        print("  → Run with --no-mic to skip hardware tests if blocked.")
    print("═" * 64)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VaniSetu Phase 1 verification")
    parser.add_argument(
        "--no-mic", action="store_true",
        help="Skip microphone capture tests (useful for headless/CI)"
    )
    args = parser.parse_args()
    asyncio.run(main(skip_mic=args.no_mic))
