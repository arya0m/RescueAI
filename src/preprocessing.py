"""
RescueAI: Text Preprocessing Module
Implements domain-specific disaster tweet cleaning, URL removal,
hashtag de-symbolization, and emergency-aware stopword filtering.
"""

import re
import html
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Ensure NLTK data path includes local workspace directory
nltk.data.path.append("./nltk_data")

# Download corpora if not already downloaded
try:
    _base_sw = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords", quiet=True)
    nltk.download("wordnet", quiet=True)
    nltk.download("omw-1.4", quiet=True)
    _base_sw = set(stopwords.words("english"))

# Whitelist domain-critical emergency words, negations, and spatial prepositions
PRESERVED_TOKENS = {
    "no", "not", "nor", "neither", "never", 
    "without", "against", "under", "over", "down", "out",
    "again", "further", "need", "needs", "help"
}

DISASTER_STOPWORDS = _base_sw - PRESERVED_TOKENS
_lemmatizer = WordNetLemmatizer()


def clean_disaster_text(text: str) -> str:
    """
    Cleans and normalizes disaster-related social media text.
    
    1. Unescapes HTML entities.
    2. Strips corrupted non-ASCII bytes.
    3. Removes web URLs.
    4. Removes RT headers and @mentions.
    5. Retains hashtag text while stripping '#' symbols.
    6. Converts to lowercase and removes non-alphabetic characters.
    7. Lemmatizes tokens while preserving emergency words and negations.
    8. Drops single/double-letter noise tokens.
    """
    if not isinstance(text, str):
        return ""
    
    # 1. Decode HTML entities and strip ASCII-corrupted bytes
    text = html.unescape(text)
    text = text.encode("ascii", "ignore").decode("ascii")
    
    # 2. Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    
    # 3. Remove Retweet headers and user mentions
    text = re.sub(r"^RT[\s]+@\w+:?", "", text)
    text = re.sub(r"@\w+", "", text)
    
    # 4. Extract hashtag keywords (keep word, remove '#')
    text = re.sub(r"#(\w+)", r"\1", text)
    
    # 5. Case folding & punctuation stripping
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    
    # 6. Tokenize, filter stopwords, and lemmatize
    tokens = [
        _lemmatizer.lemmatize(word) 
        for word in text.split() 
        if word not in DISASTER_STOPWORDS and len(word) > 2
    ]
    
    return " ".join(tokens)
