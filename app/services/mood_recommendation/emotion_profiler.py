class BookEmotionProfiler:
    def __init__(self, emotion_extractor):
        self.emotion_extractor = emotion_extractor
        self.book_profiles = {}

    def create_book_profile(self, book_id, book_title, reviews):
        """
        Create emotion profile for a book based on its reviews
        """
        # Extract emotions from all reviews
        emotion_data = self.emotion_extractor.extract_emotions_batch(reviews)

        # Store profile
        self.book_profiles[book_id] = {
            'title': book_title,
            'num_reviews': len(reviews),
            'emotion_scores': emotion_data['scores'],
            'emotion_counts': emotion_data['counts']
        }

        return self.book_profiles[book_id]

    def get_top_emotions_for_book(self, book_id, top_n=5):
        """
        Get top emotions for a specific book
        """
        if book_id not in self.book_profiles:
            return None

        scores = self.book_profiles[book_id]['emotion_scores']
        sorted_emotions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_emotions[:top_n]

    def visualize_book_emotions(self, book_id):
        """
        Visualize emotion profile for a book
        """
        if book_id not in self.book_profiles:
            print("Book not found")
            return

        profile = self.book_profiles[book_id]
        scores = profile['emotion_scores']

        # Get top 10 emotions for visualization
        top_emotions = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
        emotions = [e[0] for e in top_emotions]
        values = [e[1] for e in top_emotions]

        # Create bar plot
        plt.figure(figsize=(12, 6))
        bars = plt.bar(emotions, values, color='steelblue', alpha=0.8)

        # Color code bars
        colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(bars)))
        for bar, color in zip(bars, colors):
            bar.set_color(color)

        plt.xlabel('Emotions', fontsize=12)
        plt.ylabel('Score (%)', fontsize=12)
        plt.title(f'Emotion Profile: {profile["title"]}\n({profile["num_reviews"]} reviews analyzed)',
                  fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.grid(axis='y', alpha=0.3)
        plt.show()

# Initialize book profiler
book_profiler = BookEmotionProfiler(emotion_extractor)
print("✓ Book emotion profiler initialized")
