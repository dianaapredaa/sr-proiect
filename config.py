"""
Configuration for Movie Recommendation System
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Recombee API Configuration
RECOMBEE_DATABASE_ID = os.getenv('RECOMBEE_DATABASE_ID', 'your-database-id')
RECOMBEE_PRIVATE_TOKEN = os.getenv('RECOMBEE_PRIVATE_TOKEN', 'your-private-token')
RECOMBEE_REGION = os.getenv('RECOMBEE_REGION', 'eu-west')  # or 'us-west', 'ap-se'

# Data Paths (relative to project root)
DATA_DIR = os.getenv('DATA_DIR', 'dataset')
MOVIES_METADATA_PATH = os.path.join(DATA_DIR, 'movies_metadata.csv')
KEYWORDS_PATH = os.path.join(DATA_DIR, 'keywords.csv')
CREDITS_PATH = os.path.join(DATA_DIR, 'credits.csv')
RATINGS_PATH = os.path.join(DATA_DIR, 'ratings_small.csv')  # Folosim versiunea mică pentru demo

# Application Settings
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
PORT = int(os.getenv('PORT', 5001))  # 5001 pentru că 5000 e ocupat de AirPlay pe Mac
HOST = os.getenv('HOST', '0.0.0.0')

# Recommendation Settings
DEFAULT_NUM_RECOMMENDATIONS = 10
MIN_RATING_FOR_LIKE = 3.5  # Rating >= this is considered a "like"

# Cold Start Settings
POPULAR_MOVIES_COUNT = 20  # Number of popular movies to show new users
GENRES_FOR_COLD_START = [
    'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 
    'Documentary', 'Drama', 'Family', 'Fantasy', 'History',
    'Horror', 'Music', 'Mystery', 'Romance', 'Science Fiction',
    'Thriller', 'War', 'Western'
]

