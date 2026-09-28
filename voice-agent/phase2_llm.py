"""
VaniSetu — Phase 2: Interactive text conversation test.
Zero-audio. Just you + the LLM in your terminal.
Proves the conversation state machine and LLM wiring before adding audio.

Usage:
    .venv\\Scripts\\python.exe phase2_llm.py

What to type (simulate a call):
    "Namaste"
    "Mera naam Ramesh hai, Ranchi se hoon"
    "Main furniture banata hoon, 15 saal se"
    "10th pass hoon"
"""

import asyncio
import sys
import uuid
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load .env before importing agent (agent reads OPENROUTER_API_KEY on import)
from dotenv import load_dotenv
load_dotenv()

from conversation_states import CallState, Stage
from agent import get_response, extract_json, apply_extraction, backend_name


async def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  VaniSetu — Phase 2: LLM Conversation Test (text mode)      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"  LLM backend: {backend_name()}")
    print("  Type in Hindi or English. Type 'quit' to exit.\n")

    state = CallState(call_id=str(uuid.uuid4()))

    # ── Opening greeting ──────────────────────────────────────────────────────
    print("[Stage: greeting]")
    greeting = await get_response(state, "(call started)")
    print(f"🤖 {greeting}\n")
    state.history.append({"role": "assistant", "content": greeting})
    state.next_stage()   # greeting → identity

    # ── Conversation loop ─────────────────────────────────────────────────────
    while state.stage not in (Stage.END,):
        try:
            user = input("👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  (call ended by user)")
            break

        if user.lower() in ("quit", "q", "exit", "bye"):
            break
        if not user:
            continue

        # Skip recommendation stage in text mode — would need real backend
        if state.stage == Stage.RECOMMEND:
            print("  ℹ️  (In Phase 3 this stage calls localhost:8000 for real recommendations)")
            print("  ℹ️  Skipping to confirm in text mode.\n")
            state.next_stage()
            continue

        reply = await get_response(state, user)

        # Track history
        state.history.append({"role": "user", "content": user})
        state.history.append({"role": "assistant", "content": reply})

        # Strip JSON block before printing (it's internal, not spoken)
        import re
        spoken = re.sub(r"```json.*?```", "", reply, flags=re.DOTALL).strip()
        print(f"\n[Stage: {state.stage.value}]")
        print(f"🤖 {spoken}\n")

        # Extract structured data & advance stage if complete
        data = extract_json(reply)
        if data:
            prev_stage = state.stage
            apply_extraction(state, data)
            print(f"  📋 Extracted: {data}")
            if state.stage != prev_stage:
                print(f"  ✅ Stage complete → {state.stage.value}\n")

    # ── Final summary ─────────────────────────────────────────────────────────
    p = state.profile
    print("\n" + "═" * 64)
    print("  CONVERSATION SUMMARY")
    print("═" * 64)
    print(f"  Name:         {p.name or '—'}")
    print(f"  Age:          {p.age or '—'}")
    print(f"  District:     {p.district or '—'}")
    print(f"  Occupation:   {p.occupation or '—'}")
    print(f"  Skills:       {', '.join(p.skills) or '—'}")
    print(f"  Education:    {p.education or '—'}")
    print(f"  Stage reached: {state.stage.value}")
    print(f"  Ready for rec: {'✅ Yes' if state.ready_for_recommendation() else '❌ No (incomplete data)'}")
    print("═" * 64)
    if state.ready_for_recommendation():
        print("  ✅ Phase 2 PASSED — proceed to Phase 3 (voice server)")
    else:
        print("  ⚠️  Keep the conversation going until all fields are collected.")
    print("  → Next: .venv\\Scripts\\python.exe server.py")
    print("═" * 64)


if __name__ == "__main__":
    asyncio.run(main())
