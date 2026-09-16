"""
Input sanitization and prompt-injection detection for EviBite AI.

This is a defense-in-depth layer -- it does NOT replace the safety
guarantees already built into the Analysis agent (which never lets the
LLM make a safety decision). Its job is different: catching malformed,
oversized, or manipulative input before it reaches any agent, especially
the LLM-powered Triage stage.
"""

import re
from typing import NamedTuple

MAX_MESSAGE_LENGTH = 1000  # matches ChatRequest's existing max_length

# Control characters (excluding common whitespace like \n, \t) that have
# no legitimate reason to appear in a user's food question, but can be
# used to break log formatting or confuse downstream parsing.
_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Phrases commonly used in prompt-injection attempts -- trying to get an
# LLM to ignore its system instructions or reveal/change its behavior.
# This list is intentionally broad and pattern-based, not exhaustive --
# new phrasings will always exist, so this is one layer, not the only one.
_INJECTION_PATTERNS = [
    re.compile(r"ignore (all |any )?(previous|prior|above) instructions", re.IGNORECASE),
    re.compile(r"you are now (an?|a) ", re.IGNORECASE),
    re.compile(r"(reveal|show|print) (your |the )?(system )?prompt", re.IGNORECASE),
    re.compile(r"disregard (your|the) (rules|instructions|guidelines)", re.IGNORECASE),
    re.compile(r"act as (if|though) you (are|were)", re.IGNORECASE),
    re.compile(r"pretend (you are|to be) (an?|a) ", re.IGNORECASE),
]


class SanitizationResult(NamedTuple):
    cleaned_message: str
    is_safe: bool
    flags: list[str]


def sanitize_message(raw_message: str) -> SanitizationResult:
    """
    Clean and evaluate a raw user message before it reaches Triage.

    Returns the cleaned text plus a safety flag and list of specific
    reasons -- callers decide whether to block, log, or just proceed
    with extra caution, rather than this function silently deciding.
    """
    flags: list[str] = []

    if not raw_message or not raw_message.strip():
        return SanitizationResult(cleaned_message="", is_safe=False, flags=["empty_message"])

    if len(raw_message) > MAX_MESSAGE_LENGTH:
        flags.append("exceeds_max_length")
        raw_message = raw_message[:MAX_MESSAGE_LENGTH]

    cleaned = _CONTROL_CHAR_PATTERN.sub("", raw_message).strip()
    if cleaned != raw_message.strip():
        flags.append("control_characters_removed")

    for pattern in _INJECTION_PATTERNS:
        if pattern.search(cleaned):
            flags.append(f"possible_prompt_injection:{pattern.pattern[:30]}")

    is_safe = not any(f.startswith("possible_prompt_injection") for f in flags) and "empty_message" not in flags

    return SanitizationResult(cleaned_message=cleaned, is_safe=is_safe, flags=flags)