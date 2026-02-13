# Install required packages
!pip install nltk pandas numpy scikit-learn matplotlib seaborn wordcloud -q

import nltk
import pandas as pd
import numpy as np
import re
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

# Download NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

print("✓ All libraries imported successfully")


## Step 2: Create Comprehensive Emotion Lexicon
# Comprehensive emotion lexicon with 35+ emotions
emotion_lexicon = {
    # Primary emotions
    'happy': [
        'joy', 'joyful', 'delighted', 'excited', 'wonderful', 'fantastic', 'amazing',
        'cheerful', 'pleased', 'glad', 'content', 'satisfied', 'thrilled', 'ecstatic',
        'happy', 'happiness', 'bliss', 'blissful', 'merry', 'jolly', 'uplifting'
    ],
    
    'sad': [
        'sad', 'sadness', 'depressing', 'tragic', 'heartbreaking', 'cry', 'tears',
        'melancholy', 'sorrowful', 'miserable', 'gloomy', 'dejected', 'downcast',
        'unhappy', 'grief', 'mourning', 'somber', 'dismal', 'tearful', 'weeping'
    ],
    
    'angry': [
        'angry', 'anger', 'frustrated', 'frustration', 'annoying', 'infuriating',
        'furious', 'enraged', 'rage', 'irritated', 'irritating', 'mad', 'outraged',
        'hostile', 'bitter', 'resentful', 'aggravated', 'irate', 'fuming'
    ],
    
    'fearful': [
        'fear', 'fearful', 'scared', 'afraid', 'terrified', 'frightened', 'anxious',
        'nervous', 'worried', 'panic', 'dread', 'horror', 'terrifying', 'scary',
        'alarmed', 'threatened', 'uneasy', 'apprehensive', 'tense', 'paranoid'
    ],
    
    'surprised': [
        'surprised', 'surprise', 'shocking', 'shocked', 'amazed', 'astonished',
        'astounding', 'startled', 'unexpected', 'stunning', 'bewildered', 'dumbfounded',
        'flabbergasted', 'speechless', 'unpredictable', 'twist', 'revelation'
    ],
    
    'disgusted': [
        'disgusted', 'disgusting', 'repulsive', 'revolting', 'gross', 'nasty',
        'vile', 'sickening', 'nauseating', 'repugnant', 'offensive', 'foul',
        'distasteful', 'appalling', 'horrible', 'horrid'
    ],
    
    # Secondary emotions
    'excited': [
        'excited', 'excitement', 'enthusiastic', 'eager', 'energetic', 'pumped',
        'thrilling', 'exhilarating', 'electrifying', 'stimulating', 'invigorating',
        'spirited', 'animated', 'lively', 'dynamic'
    ],
    
    'romantic': [
        'romantic', 'romance', 'love', 'loving', 'passionate', 'affectionate',
        'tender', 'sweet', 'charming', 'intimate', 'adoring', 'devoted',
        'amorous', 'heartfelt', 'caring', 'loving', 'enchanting'
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

print(f"✓ Emotion lexicon created with {len(emotion_lexicon)} emotion categories")
print(f"✓ Total emotion keywords: {sum(len(words) for words in emotion_lexicon.values())}")


#Step 3: Text pre-processing
class TextPreprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        # Remove negation words from stopwords as they're important for emotion
        negation_words = {'not', 'no', 'never', 'neither', 'nobody', 'nothing', 'nowhere', "n't"}
        self.stop_words = self.stop_words - negation_words

    def clean_text(self, text):
        """Clean and normalize text"""
        if pd.isna(text):
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)

        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^a-zA-Z\s\.\!\?]', '', text)

        return text

    def tokenize_and_lemmatize(self, text):
        """Tokenize and lemmatize text"""
        # Tokenize
        tokens = word_tokenize(text)

        # Remove stopwords and lemmatize
        processed_tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token not in self.stop_words and len(token) > 2
        ]

        return processed_tokens

    def preprocess(self, text):
        """Complete preprocessing pipeline"""
        cleaned = self.clean_text(text)
        tokens = self.tokenize_and_lemmatize(cleaned)
        return tokens

preprocessor = TextPreprocessor()
print("✓ Text preprocessor initialized")
