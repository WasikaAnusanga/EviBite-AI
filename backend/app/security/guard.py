"""Security Guard module for input sanitization and prompt injection defense.
"""

import re

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|directions)",
    r"disregard\s+(all\s+)?(previous|prior)\s+(instructions|prompts)",
    r"forget\s+(all\s+)?(previous|prior)\s+(instructions|prompts)",
    r"system\s+prompt",
    r"reveal\s+(your\s+)?(system|hidden)\s+(instructions|prompt)",
    r"you\s+are\s+now\s+a",
    r"override\s+(all\s+)?safety\s+rules",
    r"jailbreak",
]


def sanitize_user_query(query: str) -> tuple[bool, str]:
    """Sanitizes user input query and checks for prompt injection patterns.

    Returns:
        tuple[bool, str]: (is_safe, sanitized_query_or_reason)
    """
    if not query:
        return True, ""

    query_lower = query.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, query_lower):
            return False, "Prompt injection attempt detected."

    # Basic HTML/script tag stripping
    sanitized = re.sub(r"<[^>]*>", "", query).strip()
    return True, sanitized
