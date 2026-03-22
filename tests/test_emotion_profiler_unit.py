import builtins
import sys
import types

import pytest

from app.services.mood_recommendation.emotion_profiler import (
    BookEmotionProfiler,
    get_book_profiler,
)


class _Extractor:
    def extract_emotions_batch(self, reviews):
        return {
            "scores": {"joy": 0.9, "sadness": 0.2, "curiosity": 0.5},
            "counts": {"joy": len(reviews), "sadness": 1, "curiosity": 2},
        }


def test_create_profile_and_top_emotions():
    profiler = BookEmotionProfiler(_Extractor())
    profile = profiler.create_book_profile("b1", "Book One", ["great", "nice"])

    assert profile["title"] == "Book One"
    assert profile["num_reviews"] == 2
    assert profile["emotion_scores"]["joy"] == 0.9

    top = profiler.get_top_emotions_for_book("b1", top_n=2)
    assert top == [("joy", 0.9), ("curiosity", 0.5)]

    assert profiler.get_top_emotions_for_book("missing") is None


def test_visualize_book_emotions_missing_book_with_stubbed_deps(capsys, monkeypatch):
    profiler = BookEmotionProfiler(_Extractor())

    fake_plt = types.SimpleNamespace()
    fake_np = types.SimpleNamespace(linspace=lambda a, b, n: [0.4] * n)

    monkeypatch.setitem(sys.modules, "matplotlib", types.SimpleNamespace(pyplot=fake_plt))
    monkeypatch.setitem(sys.modules, "matplotlib.pyplot", fake_plt)
    monkeypatch.setitem(sys.modules, "numpy", fake_np)

    profiler.visualize_book_emotions("unknown")
    out = capsys.readouterr().out
    assert "Book not found" in out


def test_visualize_book_emotions_import_error(monkeypatch):
    profiler = BookEmotionProfiler(_Extractor())
    profiler.create_book_profile("b1", "Book One", ["a"])

    original_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in ("matplotlib.pyplot", "numpy") or name.startswith("matplotlib"):
            raise ImportError("missing")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    with pytest.raises(ImportError, match="Visualization dependencies are missing"):
        profiler.visualize_book_emotions("b1")


def test_visualize_book_emotions_success(monkeypatch):
    profiler = BookEmotionProfiler(_Extractor())
    profiler.create_book_profile("b1", "Book One", ["a", "b"])

    class _Bar:
        def __init__(self):
            self.color = None

        def set_color(self, c):
            self.color = c

    class _Plt:
        def __init__(self):
            self.xlabel_called = False
            self.show_called = False
            self.cm = types.SimpleNamespace(RdYlGn=lambda vals: ["r"] * len(vals))

        def figure(self, **kwargs):
            return None

        def bar(self, emotions, values, color=None, alpha=None):
            return [_Bar() for _ in emotions]

        def xlabel(self, *args, **kwargs):
            self.xlabel_called = True

        def ylabel(self, *args, **kwargs):
            return None

        def title(self, *args, **kwargs):
            return None

        def xticks(self, *args, **kwargs):
            return None

        def tight_layout(self):
            return None

        def grid(self, *args, **kwargs):
            return None

        def show(self):
            self.show_called = True

    fake_plt = _Plt()
    fake_np = types.SimpleNamespace(linspace=lambda a, b, n: [0.5] * n)

    monkeypatch.setitem(sys.modules, "matplotlib", types.SimpleNamespace(pyplot=fake_plt))
    monkeypatch.setitem(sys.modules, "matplotlib.pyplot", fake_plt)
    monkeypatch.setitem(sys.modules, "numpy", fake_np)

    profiler.visualize_book_emotions("b1")
    assert fake_plt.xlabel_called is True
    assert fake_plt.show_called is True


def test_get_book_profiler_factory():
    profiler = get_book_profiler(_Extractor())
    assert isinstance(profiler, BookEmotionProfiler)
