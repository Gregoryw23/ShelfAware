class EmotionExtractor:
    def __init__(self, emotion_lexicon):
        self.emotion_lexicon = emotion_lexicon
        self.preprocessor = TextPreprocessor()

        # Create reverse mapping: word -> emotions
        self.word_to_emotions = {}
        for emotion, words in emotion_lexicon.items():
            for word in words:
                if word not in self.word_to_emotions:
                    self.word_to_emotions[word] = []
                self.word_to_emotions[word].append(emotion)

    def extract_emotions(self, review_text):
        """
        Extract emotions from review text using lexicon matching
        Returns: Dictionary with emotion counts and scores
        """
        # Preprocess text
        tokens = self.preprocessor.preprocess(review_text)

        # Initialize emotion counters
        emotion_counts = {emotion: 0 for emotion in self.emotion_lexicon.keys()}

        # Count emotion word matches
        total_matches = 0
        for token in tokens:
            if token in self.word_to_emotions:
                for emotion in self.word_to_emotions[token]:
                    emotion_counts[emotion] += 1
                    total_matches += 1

        # Calculate normalized scores (percentages)
        emotion_scores = {}
        if total_matches > 0:
            for emotion, count in emotion_counts.items():
                emotion_scores[emotion] = (count / total_matches) * 100
        else:
            emotion_scores = {emotion: 0 for emotion in emotion_counts.keys()}

        return {
            'counts': emotion_counts,
            'scores': emotion_scores,
            'total_emotion_words': total_matches,
            'total_words': len(tokens)
        }

    def get_top_emotions(self, review_text, top_n=5):
        """
        Get top N emotions from review
        """
        result = self.extract_emotions(review_text)
        scores = result['scores']

        # Sort by score and get top N
        sorted_emotions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_emotions[:top_n]

    def extract_emotions_batch(self, review_list):
        """
        Extract emotions from multiple reviews
        Returns aggregated emotion profile
        """
        aggregated_counts = {emotion: 0 for emotion in self.emotion_lexicon.keys()}
        total_reviews = len(review_list)

        for review in review_list:
            result = self.extract_emotions(review)
            for emotion, count in result['counts'].items():
                aggregated_counts[emotion] += count

        # Calculate average scores
        total_counts = sum(aggregated_counts.values())
        aggregated_scores = {}
        if total_counts > 0:
            for emotion, count in aggregated_counts.items():
                aggregated_scores[emotion] = (count / total_counts) * 100
        else:
            aggregated_scores = {emotion: 0 for emotion in aggregated_counts.keys()}

        return {
            'counts': aggregated_counts,
            'scores': aggregated_scores,
            'num_reviews': total_reviews
        }

# Initialize emotion extractor
emotion_extractor = EmotionExtractor(emotion_lexicon)
print("✓ Emotion extractor initialized")


# Test with sample reviews
test_reviews = [
    "This book was absolutely amazing! I felt so happy and excited reading every page. The characters were wonderful and the story was uplifting.",
    "A truly heartbreaking story that made me cry. So sad and depressing, but beautifully written.",
    "What a thrilling adventure! I was on the edge of my seat. So suspenseful and exciting!",
    "This romance novel was sweet and touching. Very romantic and heartwarming.",
    "Dark, disturbing, and haunting. A grim tale that left me unsettled."
]

print("Testing Emotion Extraction:\n" + "="*60)

for i, review in enumerate(test_reviews, 1):
    print(f"\nReview {i}: {review[:80]}...")
    top_emotions = emotion_extractor.get_top_emotions(review, top_n=3)
    print("Top 3 Emotions:")
    for emotion, score in top_emotions:
        if score > 0:
            print(f"  - {emotion.capitalize()}: {score:.1f}%")
