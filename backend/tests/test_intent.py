import pytest

from app.core.intent import classify_intent

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "text,expected_intent",
    [
        ("I'd like to book a table for tonight", "book_table"),
        ("Can you reserve a table for 4?", "book_table"),
        ("Is there any table available this weekend?", "check_availability"),
        ("What do you have on the menu?", "menu_question"),
        ("Do you serve vegan options?", "menu_question"),
        ("I'd like to order a cappuccino", "order_item"),
        ("Hello!", "small_talk"),
        ("Thanks a lot!", "small_talk"),
    ],
)
async def test_keyword_classification_matches_expected_intent(text, expected_intent):
    label, confidence, method = await classify_intent(text)
    assert label == expected_intent
    assert method == "keyword"
    assert confidence == 1.0


async def test_embedding_fallback_classifies_paraphrased_message():
    # No exact keyword like "book"/"reserve"/"available" — should fall through
    # to embedding similarity against the fixed labeled examples.
    label, confidence, method = await classify_intent("could you set us up with a table for six people?")
    assert method == "embedding"
    assert label == "book_table"
    assert confidence >= 0.35


async def test_gibberish_is_classified_as_unknown():
    label, confidence, method = await classify_intent("asdkjfh qwoieuqwoiue xkcvjjj")
    assert method == "unknown"
    assert label == "unknown"
