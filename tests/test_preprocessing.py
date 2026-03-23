from unittest.mock import MagicMock, patch

import pytest

from app.services.mood_recommendation import preprocessing
from app.services.mood_recommendation.preprocessing import TextPreprocessor


def make_preprocessor(stop_words=None):
    with patch.object(preprocessing.stopwords, "words", return_value=stop_words or ["the", "and", "not"]):
        return TextPreprocessor()


def test_ensure_nltk_resource_skips_download_when_present():
    with patch.object(preprocessing.nltk.data, "find") as mock_find, patch.object(
        preprocessing.nltk, "download"
    ) as mock_download:
        preprocessing._ensure_nltk_resource("tokenizers/punkt", "punkt")

    mock_find.assert_called_once_with("tokenizers/punkt")
    mock_download.assert_not_called()


def test_ensure_nltk_resource_downloads_when_missing():
    with patch.object(preprocessing.nltk.data, "find", side_effect=LookupError), patch.object(
        preprocessing.nltk, "download"
    ) as mock_download:
        preprocessing._ensure_nltk_resource("tokenizers/punkt", "punkt")

    mock_download.assert_called_once_with("punkt", quiet=True)


def test_init_preserves_negation_words():
    processor = make_preprocessor(["the", "and", "not", "never"])

    assert "the" in processor.stop_words
    assert "not" not in processor.stop_words
    assert "never" not in processor.stop_words


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, True),
        (float("nan"), True),
        ("", False),
        (0.0, False),
        ("hello", False),
    ],
)
def test_is_missing(value, expected):
    processor = make_preprocessor()
    assert processor._is_missing(value) is expected


def test_clean_text_normalizes_urls_symbols_and_whitespace():
    processor = make_preprocessor()

    cleaned = processor.clean_text(" Hello!!! Visit https://example.com NOW... #1 ")

    assert cleaned == "hello!!! visit now..."


def test_clean_text_returns_empty_for_missing_values():
    processor = make_preprocessor()
    assert processor.clean_text(None) == ""


def test_tokenize_and_lemmatize_returns_empty_for_blank_input():
    processor = make_preprocessor()
    assert processor.tokenize_and_lemmatize("") == []


def test_tokenize_and_lemmatize_filters_stopwords_and_short_tokens():
    processor = make_preprocessor(["the", "and"])
    processor.lemmatizer = MagicMock()
    processor.lemmatizer.lemmatize.side_effect = lambda token: f"lemma-{token}"

    with patch.object(preprocessing, "word_tokenize", return_value=["the", "cats", "an", "running"]):
        tokens = processor.tokenize_and_lemmatize("The cats running")

    assert tokens == ["lemma-cats", "lemma-running"]


def test_tokenize_and_lemmatize_falls_back_to_split_when_tokenizer_data_missing():
    processor = make_preprocessor(["the"])
    processor.lemmatizer = MagicMock()
    processor.lemmatizer.lemmatize.side_effect = lambda token: token.upper()

    with patch.object(preprocessing, "word_tokenize", side_effect=LookupError):
        tokens = processor.tokenize_and_lemmatize("the cat jumps")

    assert tokens == ["CAT", "JUMPS"]


def test_preprocess_runs_clean_and_tokenize_pipeline():
    processor = make_preprocessor()

    with patch.object(processor, "clean_text", return_value="cleaned") as mock_clean, patch.object(
        processor, "tokenize_and_lemmatize", return_value=["token"]
    ) as mock_tokenize:
        result = processor.preprocess("raw text")

    assert result == ["token"]
    mock_clean.assert_called_once_with("raw text")
    mock_tokenize.assert_called_once_with("cleaned")
