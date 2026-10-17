from local_rag_system.services.conversation_service import TITLE_MAX_LENGTH, make_title


def test_short_message_becomes_title_unchanged() -> None:
    assert make_title("Hello there") == "Hello there"


def test_whitespace_is_collapsed() -> None:
    assert make_title("a\n\n  b\tc") == "a b c"


def test_long_message_is_truncated_with_ellipsis() -> None:
    title = make_title("word " * 50)
    assert len(title) <= TITLE_MAX_LENGTH
    assert title.endswith("…")
