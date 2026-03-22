import pytest

from app.services.mood_recommendation.preprocessing import TextPreprocessor


@pytest.fixture
def preprocessor():
    return TextPreprocessor()


def test_is_missing_handles_none_and_nan(preprocessor):
    assert preprocessor._is_missing(None) is True
    assert preprocessor._is_missing(float("nan")) is True
    assert preprocessor._is_missing(0.0) is False
    assert preprocessor._is_missing("text") is False


def test_clean_text_normalizes_and_strips_urls(preprocessor):
    raw = "Check THIS out: https://example.com wow!!! #Amazing 123"
    cleaned = preprocessor.clean_text(raw)

    assert "https://example.com" not in cleaned
    assert cleaned == "check this out wow!!! amazing"


def test_clean_text_missing_returns_empty(preprocessor):
    assert preprocessor.clean_text(None) == ""


def test_tokenize_and_lemmatize_filters_stop_words(preprocessor, monkeypatch):
    monkeypatch.setattr(
        "app.services.mood_recommendation.preprocessing.word_tokenize",
        lambda text: ["this", "books", "are", "amazing", "not", "bad"],
    )

    # Make output deterministic regardless of WordNet data nuances.
    monkeypatch.setattr(preprocessor.lemmatizer, "lemmatize", lambda token: token.rstrip("s"))

    tokens = preprocessor.tokenize_and_lemmatize("ignored by monkeypatch")

    assert "this" not in tokens
    assert "are" not in tokens
    assert "not" in tokens
    assert tokens == ["book", "amazing", "not", "bad"]


def test_tokenize_and_lemmatize_falls_back_on_lookup_error(preprocessor, monkeypatch):
    def _raise_lookup(_text):
        raise LookupError("punkt missing")

    monkeypatch.setattr("app.services.mood_recommendation.preprocessing.word_tokenize", _raise_lookup)
    monkeypatch.setattr(preprocessor.lemmatizer, "lemmatize", lambda token: token)

    tokens = preprocessor.tokenize_and_lemmatize("calm and focused")
    assert tokens == ["calm", "focused"]


def test_tokenize_and_lemmatize_empty_text_returns_empty(preprocessor):
    assert preprocessor.tokenize_and_lemmatize("") == []


def test_preprocess_runs_full_pipeline(preprocessor, monkeypatch):
    monkeypatch.setattr(preprocessor, "clean_text", lambda text: "cleaned text")
    monkeypatch.setattr(preprocessor, "tokenize_and_lemmatize", lambda text: ["cleaned", "text"])

    assert preprocessor.preprocess("Any Input") == ["cleaned", "text"]
