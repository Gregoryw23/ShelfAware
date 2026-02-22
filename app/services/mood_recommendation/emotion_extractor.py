from app.services.mood_recommendation.preprocessing import TextPreprocessor


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


# Define emotion lexicon for emotion extraction
emotion_lexicon = {
    'happy': ['happy', 'joy', 'joyful', 'delighted', 'cheerful', 'wonderful', 'amazing', 'fantastic', 'awesome', 'great', 'brilliant', 'excellent', 'love', 'loved', 'superb', 'outstanding', 'terrific', 'marvelous', 'splendid', 'delightful'],
    'sad': ['sad', 'sadness', 'depressed', 'depressing', 'unhappy', 'tearful', 'heartbroken', 'miserable', 'disappointing', 'disappointed', 'dull', 'boring', 'drab', 'lackluster', 'tedious', 'sluggish'],
    'angry': ['angry', 'rage', 'furious', 'annoyed', 'frustrated', 'irritated', 'mad', 'hostile', 'awful', 'terrible', 'horrible', 'hate', 'hated', 'despicable'],
    'excited': ['excited', 'thrilled', 'exhilarated', 'eager', 'enthusiastic', 'energetic', 'pumped', 'awesome', 'incredible', 'unbelievable', 'phenomenal'],
    'scared': ['scared', 'afraid', 'frightened', 'terrified', 'nervous', 'anxious', 'unsettled', 'frightening', 'chilling', 'spooky', 'creepy', 'unsettling', 'horrifying'],
    'romantic': ['romantic', 'love', 'loved', 'affectionate', 'tender', 'passionate', 'intimate', 'sweet', 'beautiful', 'gorgeous', 'lovely', 'dreamy', 'swoon'],
    'suspenseful': ['suspenseful', 'suspense', 'tense', 'tension', 'thrilling', 'cliffhanger', 'gripping', 'heart-pounding', 'breathtaking', 'riveting'],
    'dark': ['dark', 'grim', 'disturbing', 'haunting', 'sinister', 'mysterious', 'eerie', 'evil', 'twisted', 'corrupt'],
    'excited': [
        'excited', 'excitement', 'enthusiastic', 'eager', 'energetic', 'pumped',
        'thrilling', 'exhilarating', 'electrifying', 'stimulating', 'invigorating',
        'spirited', 'animated', 'lively', 'dynamic',
        'awesome', 'incredible', 'unbelievable', 'phenomenal'
    ],
    
    'romantic': [
        'romantic', 'romance', 'love', 'loving', 'passionate', 'affectionate',
        'tender', 'sweet', 'charming', 'intimate', 'adoring', 'devoted',
        'amorous', 'heartfelt', 'caring', 'loving', 'enchanting',
        'beautiful', 'gorgeous', 'lovely', 'dreamy', 'swoon'
    ],
    
    'hopeful': [
        'hopeful', 'hope', 'optimistic', 'positive', 'encouraging', 'inspiring',
        'uplifting', 'promising', 'bright', 'confident', 'assured', 'faith',
        'expectant', 'aspirational', 'motivated'
    ],
    
    'nostalgic': [
        'nostalgic', 'nostalgia', 'reminiscent', 'wistful', 'sentimental',
        'bittersweet', 'longing', 'yearning', 'reflective', 'remembering',
        'memories', 'past', 'bygone', 'reminisce'
    ],
    
    'peaceful': [
        'peaceful', 'peace', 'calm', 'calming', 'serene', 'tranquil', 'relaxing',
        'soothing', 'gentle', 'quiet', 'still', 'restful', 'meditative',
        'harmonious', 'placid', 'undisturbed'
    ],
    
    'curious': [
        'curious', 'intriguing', 'mysterious', 'mystery', 'enigmatic', 'puzzling',
        'fascinating', 'interesting', 'captivating', 'compelling', 'investigative',
        'inquisitive', 'questioning', 'wondering'
    ],
    
    'tense': [
        'tense', 'tension', 'suspenseful', 'suspense', 'gripping', 'intense',
        'thrilling', 'edge', 'nail-biting', 'dramatic', 'climactic', 'stressful',
        'nerve-wracking', 'anxious', 'uneasy'
    ],
    
    'empowered': [
        'empowered', 'empowering', 'strong', 'strength', 'powerful', 'brave',
        'courageous', 'bold', 'confident', 'determined', 'resilient', 'triumphant',
        'victorious', 'inspiring', 'motivating'
    ],
    
    'lonely': [
        'lonely', 'loneliness', 'alone', 'isolated', 'solitary', 'abandoned',
        'forsaken', 'desolate', 'friendless', 'alienated', 'disconnected',
        'estranged', 'remote', 'detached'
    ],
    
    'grateful': [
        'grateful', 'gratitude', 'thankful', 'appreciative', 'blessed', 'fortunate',
        'lucky', 'indebted', 'obliged', 'recognition', 'acknowledgment'
    ],
    
    'confused': [
        'confused', 'confusion', 'perplexed', 'baffled', 'puzzled', 'bewildered',
        'disoriented', 'lost', 'uncertain', 'unclear', 'ambiguous', 'complicated',
        'complex', 'mystified'
    ],
    
    'inspired': [
        'inspired', 'inspiring', 'inspirational', 'motivating', 'enlightening',
        'thought-provoking', 'stimulating', 'creative', 'innovative', 'visionary',
        'imaginative', 'influential'
    ],
    
    'amused': [
        'amused', 'amusing', 'funny', 'humorous', 'hilarious', 'witty', 'comical',
        'entertaining', 'laugh', 'laughter', 'joke', 'comedy', 'playful',
        'lighthearted', 'cheerful'
    ],
    
    'moved': [
        'moved', 'moving', 'touching', 'emotional', 'poignant', 'heartwarming',
        'tear-jerker', 'affecting', 'stirring', 'profound', 'deep', 'meaningful',
        'powerful', 'impactful'
    ],
    
    'adventurous': [
        'adventurous', 'adventure', 'exciting', 'daring', 'bold', 'thrilling',
        'epic', 'quest', 'journey', 'exploration', 'expeditionary', 'heroic',
        'action-packed'
    ],
    
    'reflective': [
        'reflective', 'contemplative', 'thoughtful', 'introspective', 'meditative',
        'philosophical', 'deep', 'profound', 'pensive', 'analytical', 'cerebral',
        'intellectual'
    ],
    
    'dark': [
        'dark', 'darkness', 'grim', 'bleak', 'sinister', 'ominous', 'foreboding',
        'menacing', 'disturbing', 'twisted', 'macabre', 'morbid', 'haunting',
        'eerie', 'unsettling'
    ],
    
    'whimsical': [
        'whimsical', 'quirky', 'playful', 'fanciful', 'imaginative', 'magical',
        'enchanting', 'delightful', 'charming', 'lighthearted', 'fantastical',
        'dreamy', 'fairytale'
    ],
    
    'heartbroken': [
        'heartbroken', 'heartbreak', 'devastated', 'crushed', 'shattered',
        'destroyed', 'broken', 'anguished', 'tormented', 'suffering', 'pain',
        'painful', 'hurt', 'wounded'
    ],
    
    'triumphant': [
        'triumphant', 'triumph', 'victorious', 'victory', 'winning', 'successful',
        'achievement', 'accomplished', 'conquering', 'overcoming', 'glorious',
        'celebrated'
    ]
}

# Initialize emotion extractor
emotion_extractor = EmotionExtractor(emotion_lexicon)
print("✓ Emotion extractor initialized")


