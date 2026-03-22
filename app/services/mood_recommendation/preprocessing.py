import re
from typing import Any

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize


def _ensure_nltk_resource(resource_path: str, download_name: str) -> None:
    try:
        nltk.data.find(resource_path)
    except LookupError:
        nltk.download(download_name, quiet=True)


# Keep runtime dependencies minimal: only ensure resources needed by tokenizer/lemmatizer.
_ensure_nltk_resource("tokenizers/punkt", "punkt")
_ensure_nltk_resource("corpora/stopwords", "stopwords")
_ensure_nltk_resource("corpora/wordnet", "wordnet")


class TextPreprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words("english"))
        # Preserve negation words because they strongly affect sentiment/emotion.
        negation_words = {"not", "no", "never", "neither", "nobody", "nothing", "nowhere", "n't"}
        self.stop_words = self.stop_words - negation_words

    def _is_missing(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, float):
            return value != value
        return False

    def clean_text(self, text: Any) -> str:
        """Clean and normalize text before tokenization."""
        if self._is_missing(text):
            return ""

        normalized = str(text).lower()
        normalized = re.sub(r"http\S+|www\S+", "", normalized)
        # Keep letters and sentence punctuation for tokenization context.
        normalized = re.sub(r"[^a-z\s\.\!\?]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def tokenize_and_lemmatize(self, text: str) -> list[str]:
        """Tokenize, remove stopwords, and lemmatize tokens."""
        if not text:
            return []

        try:
            tokens = word_tokenize(text)
        except LookupError:
            # Graceful fallback if punkt tokenizer data is not available for any reason.
            tokens = text.split()

        processed_tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token not in self.stop_words and len(token) > 2
        ]
        return processed_tokens

    def preprocess(self, text: Any) -> list[str]:
        """Complete preprocessing pipeline used by EmotionExtractor."""
        cleaned = self.clean_text(text)
        return self.tokenize_and_lemmatize(cleaned)


preprocessor = TextPreprocessor()
