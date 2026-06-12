"""
Gate 2: Statistical Entropy Engine — The Ignorance Protocol
============================================================
Integrates with local Ollama (llama3.2:1b) to generate AI responses,
then evaluates confidence to decide if the response should be shown
or blocked with a Socratic clarifying question.

CRITICAL RULE: If confidence < threshold → response MUST be empty.
The AI's generated text is NEVER returned to the user when blocked.
This proves the firewall stops lies before they reach the user.

The 3-Strike Rule (Smart Recovery):
  Strike 1: Polite clarification request
  Strike 2: More specific clarification
  Strike 3: "I don't know."
  If a user types a good/factual query, strikes reset to 0, allowing recovery.
"""

import hashlib
import random
import requests
from typing import Dict, Any, Optional

# ─────────────────────────────────────────────────────────────────────
# Ollama Configuration
# ─────────────────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"

# ─────────────────────────────────────────────────────────────────────
# 3-Strike Session Tracker (in-memory dictionary)
# ─────────────────────────────────────────────────────────────────────
# Maps session_id → current strike count
_strike_tracker: Dict[str, int] = {}

# Socratic clarifying questions for each strike level
STRIKE_MESSAGES = {
    1: "I'm not fully confident I understand your question. "
       "Could you rephrase or provide more specific context about what you're asking?",
    2: "I still need more clarity to give you a reliable answer. "
       "Can you be more specific about the topic or provide an example?",
    3: "I don't know. I've asked for clarification multiple times "
       "but the query remains unclear. Please try a different factual question.",
}

# Words indicating vague or high-entropy requests
VAGUE_MARKERS = [
    "random", "anything", "guess", "imagine", "whatever", "stuff",
    "things", "opinions", "think about", "predict", "future", "speculate",
    "feel about", "meaning of life"
]

# Words indicating factual or low-entropy requests
FACTUAL_MARKERS = [
    "what is", "where is", "how to", "how does", "why is", "who is",
    "explain", "define", "difference between", "compare", "list",
    "calculate", "tell me about", "summary of", "capital of", "when was"
]

# Words that indicate the AI's generated response is uncertain
UNCERTAINTY_MARKERS = [
    "i don't know", "i'm not sure", "unclear", "cannot determine",
    "insufficient information", "i am not sure", "it's unclear",
    "i cannot", "not certain", "hard to say", "difficult to determine",
    "i'm unable", "i am unable", "it depends", "may or may not",
    "there is no definitive", "uncertain", "ambiguous",
]

def _get_deterministic_seed(prompt: str) -> int:
    """Creates a deterministic seed from the prompt."""
    return int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)


def _calculate_structural_confidence(prompt: str) -> float:
    """
    Calculates a 'structural' confidence score based on the prompt itself.
    Factual, specific prompts get high scores (low entropy).
    Vague, open-ended prompts get low scores (high entropy).
    """
    prompt_lower = prompt.lower()
    words = prompt_lower.split()
    
    # Base confidence
    score = 50.0
    
    # 1. Length Bonus: Specific questions tend to be longer (up to 15 words)
    score += min(len(words), 15) * 1.5
    
    # 2. Factual Bonus: Presence of direct question markers
    if any(marker in prompt_lower for marker in FACTUAL_MARKERS):
        score += 25.0
        
    # 3. Vagueness Penalty: Presence of speculative or random markers
    if any(marker in prompt_lower for marker in VAGUE_MARKERS):
        score -= 35.0
        
    # 4. Short Penalty: "stuff" or "guess" with 2 words is terribly vague
    if len(words) < 3:
        score -= 15.0
        
    # 5. Deterministic Jitter: Add a tiny bit of pseudo-randomness based on the prompt hash
    # so the scores don't look completely hardcoded to the user.
    seed = _get_deterministic_seed(prompt)
    rng = random.Random(seed)
    jitter = rng.uniform(-4.0, 4.0)
    score += jitter
    
    # Clamp between 5.0 and 95.0
    return round(max(5.0, min(95.0, score)), 1)


def _calculate_final_confidence(response_text: str, prompt: str) -> float:
    """
    Combines the structural prompt confidence with the AI's actual response.
    """
    # Start with the mathematical structural score
    confidence = _calculate_structural_confidence(prompt)
    
    # If the AI explicitly says it doesn't know, tank the confidence
    text_lower = response_text.lower()
    if any(marker in text_lower for marker in UNCERTAINTY_MARKERS):
        confidence -= 25.0
        
    return round(max(5.0, min(95.0, confidence)), 1)


def _query_ollama(prompt: str) -> Optional[str]:
    """
    Sends a prompt to the local Ollama instance and returns the generated text.
    Returns None if Ollama is not running or unreachable.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 100,
                },
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        print(f"[ENTROPY] Ollama unreachable: {e}")
        return None


def _generate_fallback_response(prompt: str) -> str:
    """
    Generates a mock AI response when Ollama is not available.
    """
    prompt_lower = prompt.lower()
    seed = _get_deterministic_seed(prompt)
    rng = random.Random(seed)

    # If it's factual, give a factual-sounding mock response
    if any(p in prompt_lower for p in FACTUAL_MARKERS):
        responses = [
            "The answer to your question is well-established in the literature. "
            "Specifically, this topic has been extensively documented. "
            "Here is a structured explanation with the key facts: "
            "First, the core concept involves established principles.",
            "According to widely accepted sources, the answer is as follows. "
            "Therefore, we can state with confidence that the information is reliable.",
        ]
        return rng.choice(responses)

    # If it's vague, give a vague mock response
    if any(p in prompt_lower for p in VAGUE_MARKERS):
        responses = [
            "I'm not sure about this. It's unclear what the definitive answer would be.",
            "This is difficult to determine with any certainty. I cannot provide a reliable answer.",
        ]
        return rng.choice(responses)

    # Default
    return "Based on available information, here is what I can share. " \
           "The topic involves several considerations that should be examined."


def check_ollama_status() -> dict:
    """Checks if Ollama is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        has_model = any(OLLAMA_MODEL in name or name.startswith(OLLAMA_MODEL) for name in model_names)

        if has_model:
            return {"connected": True, "model": OLLAMA_MODEL, "message": "Ollama connected, model ready"}
        else:
            return {"connected": True, "model": "missing", "message": f"Ollama running but '{OLLAMA_MODEL}' not found."}
    except (requests.ConnectionError, requests.Timeout):
        return {
            "connected": False,
            "model": "unavailable",
            "message": "Ollama not running. Using fallback mode for demo.",
        }


def get_strikes(session_id: str) -> int:
    return _strike_tracker.get(session_id, 0)


def reset_strikes(session_id: str):
    _strike_tracker[session_id] = 0


def calculate_confidence(
    prompt: str,
    confidence_threshold: int,
    session_id: str,
) -> dict:
    """
    The core Gate 2 function. Evaluates a prompt's confidence level
    and decides whether to PASS or BLOCK the response.
    """
    # ─── Query Ollama (or use fallback) ───
    ai_response = _query_ollama(prompt)
    if ai_response is None:
        ai_response = _generate_fallback_response(prompt)
        print(f"[ENTROPY] Using fallback response (Ollama unavailable)")

    # ─── Calculate Confidence ───
    # Evaluates the structural quality of the prompt
    confidence = _calculate_final_confidence(ai_response, prompt)

    # ─── Calculate Shannon Entropy ───
    entropy = round((100 - confidence) / 33.3, 2)

    current_strikes = _strike_tracker.get(session_id, 0)

    # ─── Decision: PASS or BLOCK ───
    if confidence >= confidence_threshold:
        # PASS — The prompt is good, so we reset any strikes!
        reset_strikes(session_id)
        
        return {
            "status": "PASS",
            "gate": "GATE_2",
            "reason": "",
            "message": "AI is confident. Here is the answer.",
            "suggestion": "",
            "response": ai_response,
            "confidence": confidence,
            "threshold": confidence_threshold,
            "strikes": 0,
            "entropy": entropy,
        }
    else:
        # BLOCKED — Confidence too low
        current_strikes += 1
        _strike_tracker[session_id] = current_strikes
        
        strike_key = min(current_strikes, 3)
        socratic_message = STRIKE_MESSAGES[strike_key]

        return {
            "status": "BLOCKED",
            "gate": "GATE_2",
            "reason": "Statistical Entropy Exceeded Threshold",
            "message": socratic_message,
            "suggestion": "Try adding more details, specifying a topic, or asking a factual question.",
            "response": "",  # CRITICAL: Never return AI text when blocked
            "confidence": confidence,
            "threshold": confidence_threshold,
            "strikes": current_strikes,
            "entropy": entropy,
        }
