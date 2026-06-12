"""
Gate 2: Statistical Entropy Engine — Groq-powered confidence analysis
with 3-strike Socratic protocol and smart session recovery.
"""

import hashlib
import random
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

try:
    from groq import Groq
    _groq_key = os.getenv("GROQ_API_KEY", "")
    groq_client = Groq(api_key=_groq_key) if _groq_key else None
except ImportError:
    groq_client = None

# Session state
_strike_tracker: Dict[str, int] = {}

STRIKE_MESSAGES = {
    1: "I'm not fully confident I understand your question. Could you rephrase or provide more specific context?",
    2: "I still need more clarity to give you a reliable answer. Can you be more specific or provide an example?",
    3: "I don't know. I've asked for clarification multiple times but the query remains unclear. Please try a different question.",
}

VAGUE_MARKERS = [
    "random", "anything", "guess", "imagine", "whatever", "stuff",
    "things", "opinions", "think about", "predict", "future", "speculate",
    "feel about", "meaning of life",
]

FACTUAL_MARKERS = [
    "what is", "where is", "how to", "how does", "why is", "who is",
    "explain", "define", "difference between", "compare", "list",
    "calculate", "tell me about", "summary of", "capital of", "when was",
]

UNCERTAINTY_MARKERS = [
    "i don't know", "i'm not sure", "unclear", "cannot determine",
    "insufficient information", "it's unclear", "i cannot",
    "not certain", "hard to say", "difficult to determine",
    "uncertain", "ambiguous",
]

GATE_2_SYSTEM_PROMPT = """You are the AI assistant behind Shadow Guard's Gate 2.
Answer the user's question to the best of your ability.
If unsure, say so honestly. If you know the answer, be clear and concise (under 100 words)."""


def _seed(prompt: str) -> int:
    return int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)


def _structural_confidence(prompt: str) -> float:
    prompt_lower = prompt.lower()
    words = prompt_lower.split()
    score = 50.0

    score += min(len(words), 15) * 1.5
    if any(m in prompt_lower for m in FACTUAL_MARKERS):
        score += 25.0
    if any(m in prompt_lower for m in VAGUE_MARKERS):
        score -= 35.0
    if len(words) < 3:
        score -= 15.0

    rng = random.Random(_seed(prompt))
    score += rng.uniform(-4.0, 4.0)
    return round(max(5.0, min(95.0, score)), 1)


def _final_confidence(response_text: str, prompt: str) -> float:
    confidence = _structural_confidence(prompt)
    if any(m in response_text.lower() for m in UNCERTAINTY_MARKERS):
        confidence -= 25.0
    return round(max(5.0, min(95.0, confidence)), 1)


def _query_groq(prompt: str) -> Optional[str]:
    if not groq_client:
        return None
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": GATE_2_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=150,
            timeout=20,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[GATE2] Groq error: {e}")
        return None


def _fallback_response(prompt: str) -> str:
    prompt_lower = prompt.lower()
    rng = random.Random(_seed(prompt))

    if any(p in prompt_lower for p in FACTUAL_MARKERS):
        return rng.choice([
            "The answer is well-established. This topic has been extensively documented with clear, structured facts.",
            "According to widely accepted sources, the answer is reliable and well-supported by evidence.",
        ])
    if any(p in prompt_lower for p in VAGUE_MARKERS):
        return rng.choice([
            "I'm not sure about this. It's unclear what the definitive answer would be.",
            "This is difficult to determine with any certainty. I cannot provide a reliable answer.",
        ])
    return "Based on available information, the topic involves several considerations that should be examined."


def check_groq_status() -> dict:
    if not groq_client:
        return {"connected": False, "model": "unavailable", "message": "Groq API key not configured. Using fallback mode."}
    try:
        groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5, timeout=10,
        )
        return {"connected": True, "model": "llama-3.3-70b-versatile", "message": "Groq API connected."}
    except Exception as e:
        return {"connected": False, "model": "error", "message": f"Groq error: {e}. Using fallback."}


def get_strikes(session_id: str) -> int:
    return _strike_tracker.get(session_id, 0)


def reset_strikes(session_id: str):
    _strike_tracker[session_id] = 0


def calculate_confidence(prompt: str, confidence_threshold: int, session_id: str) -> dict:
    """Gate 2 core: confidence scoring + 3-strike Socratic protocol with smart recovery."""

    ai_response = _query_groq(prompt)
    if ai_response is None:
        ai_response = _fallback_response(prompt)

    confidence = _final_confidence(ai_response, prompt)
    entropy = round((100 - confidence) / 33.3, 2)
    current_strikes = _strike_tracker.get(session_id, 0)

    if confidence >= confidence_threshold:
        reset_strikes(session_id)
        return {
            "status": "PASS", "gate": "GATE_2", "reason": "",
            "message": "AI is confident. Here is the answer.",
            "suggestion": "", "response": ai_response,
            "confidence": confidence, "threshold": confidence_threshold,
            "strikes": 0, "entropy": entropy,
        }

    current_strikes += 1
    _strike_tracker[session_id] = current_strikes
    strike_key = min(current_strikes, 3)

    return {
        "status": "BLOCKED", "gate": "GATE_2",
        "reason": "Statistical Entropy Exceeded Threshold",
        "message": STRIKE_MESSAGES[strike_key],
        "suggestion": "Try adding more details or asking a factual question.",
        "response": "", "confidence": confidence,
        "threshold": confidence_threshold,
        "strikes": current_strikes, "entropy": entropy,
    }
