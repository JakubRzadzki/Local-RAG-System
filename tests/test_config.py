from local_rag_system.config import Settings


def test_known_embedding_model_uses_its_calibrated_threshold() -> None:
    settings = Settings(embedding_model="nomic-embed-text:latest")
    assert settings.effective_min_score == 0.6
    assert settings.min_score_is_calibrated


def test_unknown_embedding_model_applies_no_threshold() -> None:
    settings = Settings(embedding_model="mxbai-embed-large")
    assert settings.effective_min_score == 0.0
    assert not settings.min_score_is_calibrated


def test_explicit_threshold_wins_for_any_model() -> None:
    settings = Settings(embedding_model="mxbai-embed-large", min_score=0.45)
    assert settings.effective_min_score == 0.45
    assert settings.min_score_is_calibrated
