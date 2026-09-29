"""Query preprocessing and text normalization for the retrieval pipeline.

Provides deterministic cleaning, conversational wrapper stripping, and tokenization
while preserving critical troubleshooting terms.
"""

import re
from typing import List, Set

# Core device troubleshooting terms that must never be removed as stopwords
PROTECTED_TERMS: Set[str] = {
    "battery",
    "charging",
    "charger",
    "drain",
    "drains",
    "draining",
    "screen",
    "display",
    "brightness",
    "timeout",
    "camera",
    "photo",
    "video",
    "focus",
    "blur",
    "blurry",
    "flash",
    "night",
    "lag",
    "lagging",
    "freeze",
    "freezing",
    "stutter",
    "slow",
    "performance",
    "storage",
    "memory",
    "ram",
    "navigation",
    "gesture",
    "gestures",
    "touch",
    "sensitivity",
    "refresh",
    "rate",
    "dark",
    "mode",
    "overheating",
    "hot",
    "warm",
    "heat",
    "idle",
    "app",
    "apps",
    "crash",
    "crashing",
    "reboot",
    "restart",
}

# Conversational prefixes and wrappers
CONVERSATIONAL_PREFIXES = [
    r"^why\s+is\s+my\s+(?:phone|device)\s+having\s+this\s+problem:\s*",
    r"^why\s+is\s+my\s+(?:phone|device)\s+having\s+this\s+issue:\s*",
    r"^why\s+does\s+my\s+(?:phone|device)\s+have\s+this\s+problem:\s*",
    r"^why\s+is\s+my\s+(?:phone|device)\s+",
    r"^why\s+does\s+my\s+(?:phone|device)\s+",
    r"^how\s+(?:do\s+i|can\s+i|to)\s+(?:fix|resolve|troubleshoot)\s+",
    r"^my\s+(?:phone|device)\s+is\s+experiencing\s+",
    r"^my\s+(?:phone|device)\s+has\s+an\s+issue\s+with\s+",
    r"^my\s+(?:phone|device)\s+has\s+",
    r"^i\s+(?:have|am\s+having)\s+(?:an\s+issue|a\s+problem)\s+with\s+",
    r"^i\s+need\s+help\s+with\s+",
    r"^help\s+(?:me\s+with|with)\s+",
    r"^troubleshoot\s+",
    r"^issue\s+with\s+",
    r"^problem\s+with\s+",
    r"^can\s+you\s+help\s+me\s+fix\s+",
    r"^can\s+you\s+help\s+with\s+",
]

# Standard conversational stop words (excluding protected terms)
STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
    "by", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "from", "up", "down", "out", "off", "of",
    "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "while", "as", "if", "because", "until",
    "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "s", "t", "can", "will", "just", "don", "should", "now", "i",
    "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "having", "do", "does", "did", "doing",
    "would", "could", "phone", "device",
} - PROTECTED_TERMS


def normalize_whitespace(text: str) -> str:
    """Trim leading/trailing whitespace and collapse internal spaces."""
    return re.sub(r"\s+", " ", text).strip()


def strip_conversational_wrappers(text: str) -> str:
    """Remove boilerplate conversational introductory phrases while retaining content."""
    normalized = normalize_whitespace(text)
    lower_text = normalized.lower()

    for pattern in CONVERSATIONAL_PREFIXES:
        match = re.search(pattern, lower_text, re.IGNORECASE)
        if match:
            stripped = normalized[match.end():].strip()
            # Remove trailing punctuation marks (? . !)
            stripped = re.sub(r"[?!.]+$", "", stripped).strip()
            if len(stripped.split()) >= 1:
                return stripped

    # Also clean trailing question marks/periods
    return re.sub(r"[?!.]+$", "", normalized).strip()


def preprocess_query(query: str) -> str:
    """Full preprocessing pipeline for incoming natural language queries."""
    if not query:
        return ""
    # 1. Normalize whitespace
    cleaned = normalize_whitespace(query)
    # 2. Lowercase
    cleaned_lower = cleaned.lower()
    # 3. Strip wrappers
    unwrapped = strip_conversational_wrappers(cleaned_lower)
    return unwrapped if unwrapped else cleaned_lower


def tokenize(text: str, remove_stopwords: bool = False) -> List[str]:
    """Tokenize text into alphanumeric words, optionally filtering non-protected stop words."""
    cleaned = preprocess_query(text)
    # Extract alphanumeric words and hyphens/underscores
    tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", cleaned.lower())
    if remove_stopwords:
        tokens = [t for t in tokens if t in PROTECTED_TERMS or t not in STOP_WORDS]
    return tokens
