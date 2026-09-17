import re

import numpy as np

from app.core.embeddings import embed_text

INTENT_LABELS = ["book_table", "check_availability", "menu_question", "order_item", "small_talk"]

SIMILARITY_THRESHOLD = 0.35

_KEYWORD_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bavailab(le|ility)\b|\bfree table\b|\bopen (slot|table)s?\b|\bany table\b", re.I), "check_availability"),
    (re.compile(r"\b(book|reserve|reservation)\b", re.I), "book_table"),
    (re.compile(r"\bmenu\b|\bwhat.*(do you have|do you serve|options)\b|\bdo you (have|serve)\b|\bgluten.free\b|\bvegan\b|\bvegetarian\b", re.I), "menu_question"),
    (re.compile(r"\border\b|\bcheckout\b|\bi.?d like to (get|buy|order)\b|\bcan i get\b", re.I), "order_item"),
    (re.compile(r"^\s*(hi|hello|hey|thanks|thank you|bye|goodbye|good (morning|afternoon|evening))\b", re.I), "small_talk"),
]

# Fixed labeled examples for embedding-similarity fallback, per the plan's design:
# classify against a small fixed set of labeled examples before ever calling an LLM.
_INTENT_EXAMPLES: dict[str, list[str]] = {
    "book_table": [
        "I want a table for four tonight at 7pm",
        "Can you set us up with a table for two tomorrow evening?",
        "We'd like to come in for dinner this Friday, party of six",
    ],
    "check_availability": [
        "Do you have anything open this Friday around 8?",
        "Is there space for six people tomorrow?",
        "What times are free this weekend?",
    ],
    "menu_question": [
        "What desserts do you have?",
        "Show me your coffee selection",
        "Is there anything cold and chocolatey on the menu?",
    ],
    "order_item": [
        "I'd like two croissants to go",
        "Can I get a cappuccino for pickup",
        "I want to order a sandwich",
    ],
    "small_talk": [
        "Good morning!",
        "Thanks so much, appreciate it",
        "See you later, bye!",
    ],
}

_example_embeddings_cache: dict[str, list[np.ndarray]] | None = None


async def _get_example_embeddings() -> dict[str, list[np.ndarray]]:
    global _example_embeddings_cache
    if _example_embeddings_cache is None:
        cache: dict[str, list[np.ndarray]] = {}
        for label, examples in _INTENT_EXAMPLES.items():
            cache[label] = [np.array(await embed_text(example)) for example in examples]
        _example_embeddings_cache = cache
    return _example_embeddings_cache


def _classify_by_keywords(text: str) -> str | None:
    for pattern, label in _KEYWORD_RULES:
        if pattern.search(text):
            return label
    return None


async def _classify_by_embedding(text: str) -> tuple[str, float]:
    query_vector = np.array(await embed_text(text))
    examples = await _get_example_embeddings()

    best_label, best_score = "unknown", -1.0
    for label, vectors in examples.items():
        for vector in vectors:
            score = float(np.dot(query_vector, vector))
            if score > best_score:
                best_label, best_score = label, score

    return best_label, best_score


async def classify_intent(text: str) -> tuple[str, float, str]:
    """Classify a chat message locally, without any LLM call.

    Returns (label, confidence, method). method is "keyword", "embedding", or
    "unknown" (below the similarity threshold — the caller may then escalate
    to a single small LLM classification call).
    """
    keyword_label = _classify_by_keywords(text)
    if keyword_label is not None:
        return keyword_label, 1.0, "keyword"

    label, score = await _classify_by_embedding(text)
    if score >= SIMILARITY_THRESHOLD:
        return label, score, "embedding"

    return "unknown", score, "unknown"
