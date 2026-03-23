import pytest
from unittest.mock import MagicMock, patch
from app.services.mood_recommendation.emotion_extractor import EmotionExtractor


# Fixtures

@pytest.fixture
def simple_lexicon():
    """Minimal lexicon for predictable testing."""
    return {
        'happy': ['happy', 'joyful', 'wonderful'],
        'sad': ['sad', 'miserable', 'depressed'],
        'angry': ['angry', 'furious', 'mad'],
        'excited': ['excited', 'thrilled', 'energetic'],
    }


@pytest.fixture
def mock_preprocessor():
    """Mock TextPreprocessor."""
    preprocessor = MagicMock()
    return preprocessor


@pytest.fixture
def extractor(simple_lexicon):
    """EmotionExtractor with simple lexicon and real preprocessor."""
    return EmotionExtractor(simple_lexicon)


@pytest.fixture
def extractor_with_mock_preprocessor(simple_lexicon, mock_preprocessor):
    """EmotionExtractor where preprocessor is replaced with a mock after init."""
    ext = EmotionExtractor(simple_lexicon)
    ext.preprocessor = mock_preprocessor
    return ext, mock_preprocessor

# __init__

class TestInit:
    def test_stores_emotion_lexicon(self, simple_lexicon):
        ext = EmotionExtractor(simple_lexicon)
        assert ext.emotion_lexicon == simple_lexicon

    def test_word_to_emotions_mapping_built(self, simple_lexicon):
        ext = EmotionExtractor(simple_lexicon)
        assert 'happy' in ext.word_to_emotions
        assert 'happy' in ext.word_to_emotions['happy']

    def test_shared_word_maps_to_multiple_emotions(self):
        """A word appearing in multiple emotions should map to all of them."""
        lexicon = {
            'happy': ['bright'],
            'hopeful': ['bright'],
        }
        ext = EmotionExtractor(lexicon)
        assert set(ext.word_to_emotions['bright']) == {'happy', 'hopeful'}

    def test_all_words_in_lexicon_are_mapped(self, simple_lexicon):
        ext = EmotionExtractor(simple_lexicon)
        all_words = [word for words in simple_lexicon.values() for word in words]
        for word in all_words:
            assert word in ext.word_to_emotions

    def test_preprocessor_is_initialized(self, extractor):
        assert extractor.preprocessor is not None



# extract_emotions

class TestExtractEmotions:
    def test_returns_required_keys(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy']
        result = ext.extract_emotions("happy text")
        assert set(result.keys()) == {'counts', 'scores', 'total_emotion_words', 'total_words'}

    def test_counts_emotion_words_correctly(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy', 'joyful']
        result = ext.extract_emotions("happy joyful")
        assert result['counts']['happy'] == 2

    def test_scores_sum_to_100_when_matches_exist(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy', 'sad', 'excited']
        result = ext.extract_emotions("some text")
        assert abs(sum(result['scores'].values()) - 100.0) < 0.01

    def test_all_scores_zero_when_no_matches(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['xyz', 'abc']  # unknown words
        result = ext.extract_emotions("xyz abc")
        assert all(score == 0 for score in result['scores'].values())

    def test_total_emotion_words_correct(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy', 'sad', 'xyz']
        result = ext.extract_emotions("happy sad xyz")
        assert result['total_emotion_words'] == 2  # xyz is unknown

    def test_total_words_equals_token_count(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy', 'sad', 'xyz']
        result = ext.extract_emotions("any text")
        assert result['total_words'] == 3

    def test_empty_text_returns_zero_counts(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = []
        result = ext.extract_emotions("")
        assert result['total_emotion_words'] == 0
        assert result['total_words'] == 0
        assert all(s == 0 for s in result['scores'].values())

    def test_all_emotions_present_in_counts(self, extractor_with_mock_preprocessor, simple_lexicon):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy']
        result = ext.extract_emotions("happy")
        for emotion in simple_lexicon.keys():
            assert emotion in result['counts']

    def test_score_reflects_proportion(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        # 1 happy word, 1 sad word → each should be 50%
        mock_prep.preprocess.return_value = ['happy', 'sad']
        result = ext.extract_emotions("happy sad")
        assert result['scores']['happy'] == 50.0
        assert result['scores']['sad'] == 50.0

    def test_repeated_emotion_word_increases_count(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy', 'happy', 'happy']
        result = ext.extract_emotions("happy happy happy")
        assert result['counts']['happy'] == 3



# get_top_emotions

class TestGetTopEmotions:
    def test_returns_list_of_tuples(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy']
        result = ext.get_top_emotions("happy")
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)

    def test_default_top_n_is_5(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy', 'sad', 'angry', 'excited']
        result = ext.get_top_emotions("text")
        assert len(result) <= 5

    def test_custom_top_n(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy', 'sad', 'angry']
        result = ext.get_top_emotions("text", top_n=2)
        assert len(result) == 2

    def test_results_sorted_descending(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy', 'happy', 'sad']
        result = ext.get_top_emotions("text", top_n=4)
        scores = [score for _, score in result]
        assert scores == sorted(scores, reverse=True)

    def test_top_emotion_is_most_frequent(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        # 3 happy words vs 1 sad → happy should be top
        mock_prep.preprocess.return_value = ['happy', 'happy', 'happy', 'sad']
        result = ext.get_top_emotions("text", top_n=1)
        assert result[0][0] == 'happy'

    def test_top_n_zero_returns_empty(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy']
        result = ext.get_top_emotions("happy", top_n=0)
        assert result == []

    def test_top_n_exceeds_emotions_returns_all(self, extractor_with_mock_preprocessor, simple_lexicon):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy']
        result = ext.get_top_emotions("happy", top_n=100)
        assert len(result) == len(simple_lexicon)



# extract_emotions_batch

class TestExtractEmotionsBatch:
    def test_returns_required_keys(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy']
        result = ext.extract_emotions_batch(["happy review"])
        assert set(result.keys()) == {'counts', 'scores', 'num_reviews'}

    def test_num_reviews_is_correct(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy']
        reviews = ["review one", "review two", "review three"]
        result = ext.extract_emotions_batch(reviews)
        assert result['num_reviews'] == 3

    def test_empty_batch_returns_zero_scores(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        result = ext.extract_emotions_batch([])
        assert result['num_reviews'] == 0
        assert all(s == 0 for s in result['scores'].values())

    def test_aggregates_counts_across_reviews(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        # Each call to preprocess returns 1 'happy' token
        mock_prep.preprocess.return_value = ['happy']
        result = ext.extract_emotions_batch(["r1", "r2", "r3"])
        assert result['counts']['happy'] == 3

    def test_scores_sum_to_100(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy', 'sad']
        result = ext.extract_emotions_batch(["r1", "r2"])
        assert abs(sum(result['scores'].values()) - 100.0) < 0.01

    def test_all_emotions_present_in_output(self, extractor_with_mock_preprocessor, simple_lexicon):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy']
        result = ext.extract_emotions_batch(["happy"])
        for emotion in simple_lexicon.keys():
            assert emotion in result['counts']
            assert emotion in result['scores']

    def test_preprocessor_called_once_per_review(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy']
        reviews = ["r1", "r2", "r3"]
        ext.extract_emotions_batch(reviews)
        assert mock_prep.preprocess.call_count == 3

    def test_single_review_matches_extract_emotions(self, extractor_with_mock_preprocessor):
        ext, mock_prep = extractor_with_mock_preprocessor
        mock_prep.preprocess.return_value = ['happy', 'sad']
        single_result = ext.extract_emotions("text")
        mock_prep.preprocess.reset_mock()
        mock_prep.preprocess.return_value = ['happy', 'sad']
        batch_result = ext.extract_emotions_batch(["text"])
        assert single_result['counts'] == batch_result['counts']