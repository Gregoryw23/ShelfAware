import pytest
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock
from app.services.mood_recommendation.emotion_profiler import BookEmotionProfiler, get_book_profiler



# Fixtures

@pytest.fixture
def mock_emotion_extractor():
    """Mock emotion extractor that returns predictable data."""
    extractor = MagicMock()
    extractor.extract_emotions_batch.return_value = {
        'scores': {
            'joy': 75.0,
            'sadness': 20.0,
            'anger': 5.0,
            'fear': 10.0,
            'surprise': 30.0,
            'disgust': 3.0,
            'trust': 60.0,
            'anticipation': 45.0,
            'love': 55.0,
            'optimism': 40.0,
        },
        'counts': {
            'joy': 15,
            'sadness': 4,
            'anger': 1,
            'fear': 2,
            'surprise': 6,
            'disgust': 1,
            'trust': 12,
            'anticipation': 9,
            'love': 11,
            'optimism': 8,
        }
    }
    return extractor


@pytest.fixture
def profiler(mock_emotion_extractor):
    """BookEmotionProfiler with a mocked extractor."""
    return BookEmotionProfiler(mock_emotion_extractor)


@pytest.fixture
def sample_reviews():
    return [
        "This book was absolutely joyful and uplifting!",
        "I loved the characters and felt so much trust in the story.",
        "A bit sad in places but ultimately hopeful.",
    ]


@pytest.fixture
def profiler_with_book(profiler, sample_reviews):
    """Profiler that already has one book profile created."""
    profiler.create_book_profile("book_1", "The Great Adventure", sample_reviews)
    return profiler


# __init__

class TestInit:
    def test_stores_emotion_extractor(self, mock_emotion_extractor):
        profiler = BookEmotionProfiler(mock_emotion_extractor)
        assert profiler.emotion_extractor is mock_emotion_extractor

    def test_book_profiles_starts_empty(self, mock_emotion_extractor):
        profiler = BookEmotionProfiler(mock_emotion_extractor)
        assert profiler.book_profiles == {}


# create_book_profile

class TestCreateBookProfile:
    def test_returns_profile_dict(self, profiler, sample_reviews):
        profile = profiler.create_book_profile("book_1", "The Great Adventure", sample_reviews)
        assert isinstance(profile, dict)

    def test_profile_contains_required_keys(self, profiler, sample_reviews):
        profile = profiler.create_book_profile("book_1", "The Great Adventure", sample_reviews)
        assert set(profile.keys()) == {'title', 'num_reviews', 'emotion_scores', 'emotion_counts'}

    def test_profile_stores_correct_title(self, profiler, sample_reviews):
        profile = profiler.create_book_profile("book_1", "The Great Adventure", sample_reviews)
        assert profile['title'] == "The Great Adventure"

    def test_profile_stores_correct_num_reviews(self, profiler, sample_reviews):
        profile = profiler.create_book_profile("book_1", "The Great Adventure", sample_reviews)
        assert profile['num_reviews'] == len(sample_reviews)

    def test_profile_is_saved_in_book_profiles(self, profiler, sample_reviews):
        profiler.create_book_profile("book_1", "The Great Adventure", sample_reviews)
        assert "book_1" in profiler.book_profiles

    def test_calls_extract_emotions_batch_with_reviews(self, profiler, mock_emotion_extractor, sample_reviews):
        profiler.create_book_profile("book_1", "The Great Adventure", sample_reviews)
        mock_emotion_extractor.extract_emotions_batch.assert_called_once_with(sample_reviews)

    def test_multiple_books_stored_independently(self, profiler, mock_emotion_extractor, sample_reviews):
        profiler.create_book_profile("book_1", "Book One", sample_reviews)
        profiler.create_book_profile("book_2", "Book Two", sample_reviews)
        assert "book_1" in profiler.book_profiles
        assert "book_2" in profiler.book_profiles
        assert profiler.book_profiles["book_1"]['title'] == "Book One"
        assert profiler.book_profiles["book_2"]['title'] == "Book Two"

    def test_overwrite_existing_book_profile(self, profiler, sample_reviews):
        profiler.create_book_profile("book_1", "Old Title", sample_reviews)
        profiler.create_book_profile("book_1", "New Title", sample_reviews)
        assert profiler.book_profiles["book_1"]['title'] == "New Title"

    def test_empty_reviews_list(self, profiler):
        profile = profiler.create_book_profile("book_empty", "Empty Book", [])
        assert profile['num_reviews'] == 0


# ──────────────────────────────────────────────
# get_top_emotions_for_book
# ──────────────────────────────────────────────

class TestGetTopEmotionsForBook:
    def test_returns_none_for_unknown_book(self, profiler):
        assert profiler.get_top_emotions_for_book("nonexistent") is None

    def test_returns_list_of_tuples(self, profiler_with_book):
        result = profiler_with_book.get_top_emotions_for_book("book_1")
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)

    def test_default_top_n_is_5(self, profiler_with_book):
        result = profiler_with_book.get_top_emotions_for_book("book_1")
        assert len(result) == 5

    def test_custom_top_n(self, profiler_with_book):
        result = profiler_with_book.get_top_emotions_for_book("book_1", top_n=3)
        assert len(result) == 3

    def test_top_n_larger_than_available_emotions(self, profiler_with_book):
        result = profiler_with_book.get_top_emotions_for_book("book_1", top_n=100)
        assert len(result) == 10  # Only 10 emotions exist in mock data

    def test_results_are_sorted_descending(self, profiler_with_book):
        result = profiler_with_book.get_top_emotions_for_book("book_1", top_n=10)
        scores = [score for _, score in result]
        assert scores == sorted(scores, reverse=True)

    def test_top_emotion_is_correct(self, profiler_with_book):
        result = profiler_with_book.get_top_emotions_for_book("book_1", top_n=1)
        assert result[0] == ('joy', 75.0)  # Highest score in mock data

    def test_top_n_zero_returns_empty_list(self, profiler_with_book):
        result = profiler_with_book.get_top_emotions_for_book("book_1", top_n=0)
        assert result == []


# get_book_profiler (factory function)

class TestGetBookProfiler:
    def test_returns_book_emotion_profiler_instance(self, mock_emotion_extractor):
        result = get_book_profiler(mock_emotion_extractor)
        assert isinstance(result, BookEmotionProfiler)

    def test_returned_profiler_uses_given_extractor(self, mock_emotion_extractor):
        result = get_book_profiler(mock_emotion_extractor)
        assert result.emotion_extractor is mock_emotion_extractor

    def test_each_call_returns_new_instance(self, mock_emotion_extractor):
        profiler_a = get_book_profiler(mock_emotion_extractor)
        profiler_b = get_book_profiler(mock_emotion_extractor)
        assert profiler_a is not profiler_b


class TestVisualizeBookEmotions:
    def test_raises_import_error_when_visualization_dependencies_missing(self, profiler_with_book, monkeypatch):
        original_import = __import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in {"matplotlib.pyplot", "numpy"}:
                raise ImportError("missing dependency")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr("builtins.__import__", fake_import)

        with pytest.raises(ImportError, match="Visualization dependencies are missing"):
            profiler_with_book.visualize_book_emotions("book_1")

    def test_returns_early_when_book_profile_missing(self, profiler, monkeypatch, capsys):
        fake_pyplot = ModuleType("matplotlib.pyplot")
        fake_pyplot.cm = SimpleNamespace(RdYlGn=lambda values: values)
        fake_pyplot.figure = MagicMock()
        fake_pyplot.bar = MagicMock(return_value=[])
        fake_pyplot.xlabel = MagicMock()
        fake_pyplot.ylabel = MagicMock()
        fake_pyplot.title = MagicMock()
        fake_pyplot.xticks = MagicMock()
        fake_pyplot.tight_layout = MagicMock()
        fake_pyplot.grid = MagicMock()
        fake_pyplot.show = MagicMock()
        fake_matplotlib = ModuleType("matplotlib")
        fake_numpy = ModuleType("numpy")
        fake_numpy.linspace = MagicMock(return_value=[])

        monkeypatch.setitem(sys.modules, "matplotlib", fake_matplotlib)
        monkeypatch.setitem(sys.modules, "matplotlib.pyplot", fake_pyplot)
        monkeypatch.setitem(sys.modules, "numpy", fake_numpy)

        profiler.visualize_book_emotions("missing-book")

        assert "Book not found" in capsys.readouterr().out
        fake_pyplot.figure.assert_not_called()

    def test_visualize_book_emotions_plots_profile(self, profiler_with_book, monkeypatch):
        class FakeBar:
            def __init__(self):
                self.colors = []

            def set_color(self, color):
                self.colors.append(color)

        bars = [FakeBar(), FakeBar()]
        fake_pyplot = ModuleType("matplotlib.pyplot")
        fake_pyplot.cm = SimpleNamespace(RdYlGn=lambda values: ["c1", "c2"])
        fake_pyplot.figure = MagicMock()
        fake_pyplot.bar = MagicMock(return_value=bars)
        fake_pyplot.xlabel = MagicMock()
        fake_pyplot.ylabel = MagicMock()
        fake_pyplot.title = MagicMock()
        fake_pyplot.xticks = MagicMock()
        fake_pyplot.tight_layout = MagicMock()
        fake_pyplot.grid = MagicMock()
        fake_pyplot.show = MagicMock()
        fake_matplotlib = ModuleType("matplotlib")
        fake_numpy = ModuleType("numpy")
        fake_numpy.linspace = MagicMock(return_value=[0.3, 0.9])

        monkeypatch.setitem(sys.modules, "matplotlib", fake_matplotlib)
        monkeypatch.setitem(sys.modules, "matplotlib.pyplot", fake_pyplot)
        monkeypatch.setitem(sys.modules, "numpy", fake_numpy)

        profiler_with_book.visualize_book_emotions("book_1")

        fake_pyplot.figure.assert_called_once_with(figsize=(12, 6))
        fake_pyplot.bar.assert_called_once()
        fake_numpy.linspace.assert_called_once()
        fake_pyplot.show.assert_called_once()
        assert bars[0].colors == ["c1"]
        assert bars[1].colors == ["c2"]
