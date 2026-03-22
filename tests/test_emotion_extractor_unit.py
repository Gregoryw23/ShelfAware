from app.services.mood_recommendation.emotion_extractor import EmotionExtractor


def test_init_builds_reverse_word_mapping():
    lexicon = {
        "happy": ["joy", "great"],
        "excited": ["joy", "thrill"],
    }

    extractor = EmotionExtractor(lexicon)

    assert extractor.word_to_emotions["joy"] == ["happy", "excited"]
    assert extractor.word_to_emotions["great"] == ["happy"]


def test_extract_emotions_scores_and_counts(monkeypatch):
    lexicon = {
        "happy": ["joy", "great"],
        "sad": ["down"],
    }
    extractor = EmotionExtractor(lexicon)

    monkeypatch.setattr(extractor.preprocessor, "preprocess", lambda text: ["joy", "down", "joy", "none"])

    result = extractor.extract_emotions("ignored")

    assert result["counts"] == {"happy": 2, "sad": 1}
    assert result["total_emotion_words"] == 3
    assert result["total_words"] == 4
    assert round(result["scores"]["happy"], 2) == 66.67
    assert round(result["scores"]["sad"], 2) == 33.33


def test_extract_emotions_handles_zero_matches(monkeypatch):
    lexicon = {
        "happy": ["joy"],
        "sad": ["down"],
    }
    extractor = EmotionExtractor(lexicon)
    monkeypatch.setattr(extractor.preprocessor, "preprocess", lambda text: ["neutral", "plain"])

    result = extractor.extract_emotions("ignored")

    assert result["total_emotion_words"] == 0
    assert result["scores"] == {"happy": 0, "sad": 0}


def test_get_top_emotions_sorted_and_capped(monkeypatch):
    lexicon = {
        "happy": ["joy"],
        "sad": ["down"],
        "excited": ["thrill"],
    }
    extractor = EmotionExtractor(lexicon)

    monkeypatch.setattr(
        extractor,
        "extract_emotions",
        lambda _text: {
            "scores": {"happy": 70.0, "excited": 20.0, "sad": 10.0},
            "counts": {},
            "total_emotion_words": 0,
            "total_words": 0,
        },
    )

    top_two = extractor.get_top_emotions("text", top_n=2)
    assert top_two == [("happy", 70.0), ("excited", 20.0)]


def test_extract_emotions_batch_aggregates_reviews(monkeypatch):
    lexicon = {
        "happy": ["joy"],
        "sad": ["down"],
    }
    extractor = EmotionExtractor(lexicon)

    per_review_counts = {
        "r1": {"happy": 2, "sad": 1},
        "r2": {"happy": 0, "sad": 3},
        "r3": {"happy": 1, "sad": 0},
    }

    def _fake_extract(review):
        return {
            "counts": per_review_counts[review],
            "scores": {},
            "total_emotion_words": 0,
            "total_words": 0,
        }

    monkeypatch.setattr(extractor, "extract_emotions", _fake_extract)

    result = extractor.extract_emotions_batch(["r1", "r2", "r3"])

    assert result["num_reviews"] == 3
    assert result["counts"] == {"happy": 3, "sad": 4}
    assert round(result["scores"]["happy"], 2) == 42.86
    assert round(result["scores"]["sad"], 2) == 57.14


def test_extract_emotions_batch_zero_total_counts(monkeypatch):
    lexicon = {
        "happy": ["joy"],
        "sad": ["down"],
    }
    extractor = EmotionExtractor(lexicon)

    monkeypatch.setattr(
        extractor,
        "extract_emotions",
        lambda _review: {
            "counts": {"happy": 0, "sad": 0},
            "scores": {},
            "total_emotion_words": 0,
            "total_words": 0,
        },
    )

    result = extractor.extract_emotions_batch(["a", "b"])
    assert result["counts"] == {"happy": 0, "sad": 0}
    assert result["scores"] == {"happy": 0, "sad": 0}
