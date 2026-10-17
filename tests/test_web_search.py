from local_rag_system.repositories.web_search_repository import _clean


def test_lone_surrogates_are_replaced() -> None:
    cleaned = _clean("ok \udc8f done")
    assert cleaned == "ok ? done"
    cleaned.encode("utf-8")  # must not raise


def test_normal_text_is_unchanged() -> None:
    assert _clean("Zażółć gęślą jaźń") == "Zażółć gęślą jaźń"
