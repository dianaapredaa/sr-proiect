"""
Data Loader Module - Încărcarea și procesarea datelor din Kaggle Movies Dataset
"""
import ast
import pandas as pd
import numpy as np
from tqdm import tqdm
import config


def safe_literal_eval(val):
    """Evaluează în siguranță string-uri JSON-like."""
    if pd.isna(val):
        return []
    try:
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        return []


def extract_names(obj_list, key='name', max_items=5):
    """Extrage valorile pentru o cheie dintr-o listă de dicționare."""
    if not isinstance(obj_list, list):
        return []
    return [item.get(key, '') for item in obj_list[:max_items] if isinstance(item, dict)]


def load_movies_metadata(filepath=None):
    """
    Încarcă și procesează movies_metadata.csv
    
    Returns:
        DataFrame cu coloanele: id, title, overview, genres, release_date, 
                               vote_average, vote_count, runtime, poster_path
    """
    filepath = filepath or config.MOVIES_METADATA_PATH
    print(f"📚 Încărcare movies_metadata.csv din {filepath}...")
    
    # Specificăm tipurile de date pentru a evita warnings
    dtype = {
        'adult': str,
        'budget': str,
        'id': str,
        'original_title': str,
        'popularity': str,
        'poster_path': str,
        'release_date': str,
        'revenue': str,
        'runtime': str,
        'title': str,
        'vote_average': str,
        'vote_count': str
    }
    
    df = pd.read_csv(filepath, low_memory=False, dtype=dtype)
    
    # Convertim id-urile la numeric și eliminăm rândurile invalide
    df['id'] = pd.to_numeric(df['id'], errors='coerce')
    df = df.dropna(subset=['id'])
    df['id'] = df['id'].astype(int)
    
    # Procesăm genurile
    print("🎭 Procesare genuri...")
    df['genres'] = df['genres'].apply(safe_literal_eval)
    df['genre_names'] = df['genres'].apply(lambda x: extract_names(x))
    df['genres_str'] = df['genre_names'].apply(lambda x: ', '.join(x) if x else '')
    
    # Convertim valorile numerice
    df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce').fillna(0)
    df['vote_count'] = pd.to_numeric(df['vote_count'], errors='coerce').fillna(0)
    df['runtime'] = pd.to_numeric(df['runtime'], errors='coerce').fillna(0)
    
    # Curățăm overview
    df['overview'] = df['overview'].fillna('')
    
    # Selectăm coloanele relevante
    result = df[['id', 'title', 'overview', 'genre_names', 'genres_str', 
                 'release_date', 'vote_average', 'vote_count', 'runtime', 
                 'poster_path']].copy()
    
    print(f"✅ Încărcate {len(result)} filme")
    return result


def load_keywords(filepath=None):
    """
    Încarcă și procesează keywords.csv
    
    Returns:
        DataFrame cu coloanele: id, keywords
    """
    filepath = filepath or config.KEYWORDS_PATH
    print(f"🔑 Încărcare keywords.csv din {filepath}...")
    
    df = pd.read_csv(filepath)
    
    # Procesăm keywords
    df['keywords'] = df['keywords'].apply(safe_literal_eval)
    df['keyword_names'] = df['keywords'].apply(lambda x: extract_names(x))
    df['keywords_str'] = df['keyword_names'].apply(lambda x: ', '.join(x) if x else '')
    
    result = df[['id', 'keyword_names', 'keywords_str']].copy()
    print(f"✅ Încărcate keywords pentru {len(result)} filme")
    return result


def load_credits(filepath=None):
    """
    Încarcă și procesează credits.csv pentru a extrage regizori și actori.
    
    Returns:
        DataFrame cu coloanele: id, director, actors
    """
    filepath = filepath or config.CREDITS_PATH
    print(f"🎬 Încărcare credits.csv din {filepath}...")
    
    df = pd.read_csv(filepath)
    
    # Procesăm cast (actori)
    df['cast'] = df['cast'].apply(safe_literal_eval)
    df['actors'] = df['cast'].apply(lambda x: extract_names(x, max_items=5))
    df['actors_str'] = df['actors'].apply(lambda x: ', '.join(x) if x else '')
    
    # Procesăm crew pentru a găsi regizorul
    df['crew'] = df['crew'].apply(safe_literal_eval)
    df['director'] = df['crew'].apply(lambda x: 
        next((member['name'] for member in x 
              if isinstance(member, dict) and member.get('job') == 'Director'), ''))
    
    result = df[['id', 'director', 'actors', 'actors_str']].copy()
    print(f"✅ Încărcate credits pentru {len(result)} filme")
    return result


def load_ratings(filepath=None, sample_size=None):
    """
    Încarcă ratings.csv
    
    Args:
        filepath: Calea către fișier
        sample_size: Dacă e specificat, încarcă doar un sample
        
    Returns:
        DataFrame cu coloanele: userId, movieId, rating, timestamp
    """
    filepath = filepath or config.RATINGS_PATH
    print(f"⭐ Încărcare ratings.csv din {filepath}...")
    
    if sample_size:
        # Încărcăm doar un sample pentru testare
        df = pd.read_csv(filepath, nrows=sample_size)
        print(f"✅ Încărcate {len(df)} ratings (sample)")
    else:
        # Încărcăm tot fișierul
        df = pd.read_csv(filepath)
        print(f"✅ Încărcate {len(df):,} ratings")
    
    return df


def merge_movie_data(movies_df, keywords_df=None, credits_df=None):
    """
    Combină toate datele despre filme într-un singur DataFrame.
    
    Returns:
        DataFrame complet cu toate informațiile despre filme
    """
    print("🔄 Combinare date filme...")
    
    result = movies_df.copy()
    
    if keywords_df is not None:
        result = result.merge(keywords_df, on='id', how='left')
        result['keyword_names'] = result['keyword_names'].apply(
            lambda x: x if isinstance(x, list) else [])
        result['keywords_str'] = result['keywords_str'].fillna('')
    
    if credits_df is not None:
        result = result.merge(credits_df, on='id', how='left')
        result['director'] = result['director'].fillna('')
        result['actors'] = result['actors'].apply(
            lambda x: x if isinstance(x, list) else [])
        result['actors_str'] = result['actors_str'].fillna('')
    
    print(f"✅ Date combinate pentru {len(result)} filme")
    return result


def prepare_movies_for_recombee(movies_df):
    """
    Pregătește datele pentru încărcarea în Recombee.
    
    Returns:
        List de dicționare, fiecare reprezentând un film cu toate atributele
    """
    print("📦 Pregătire date pentru Recombee...")
    
    movies = []
    for _, row in tqdm(movies_df.iterrows(), total=len(movies_df), desc="Procesare filme"):
        movie = {
            'item_id': str(row['id']),
            'title': str(row.get('title', '')),
            'overview': str(row.get('overview', ''))[:1000],  # Limităm la 1000 caractere
            'genres': row.get('genre_names', []) if isinstance(row.get('genre_names'), list) else [],
            'release_date': str(row.get('release_date', '')),
            'vote_average': float(row.get('vote_average', 0)),
            'vote_count': int(row.get('vote_count', 0)),
            'runtime': int(row.get('runtime', 0)),
            'poster_path': str(row.get('poster_path', '')) if pd.notna(row.get('poster_path')) else '',
        }
        
        # Adăugăm keywords dacă există
        if 'keyword_names' in row and isinstance(row['keyword_names'], list):
            movie['keywords'] = row['keyword_names'][:10]  # Max 10 keywords
        
        # Adăugăm director și actori dacă există
        if 'director' in row:
            movie['director'] = str(row['director'])
        if 'actors' in row and isinstance(row['actors'], list):
            movie['actors'] = row['actors'][:5]  # Max 5 actori
        
        movies.append(movie)
    
    print(f"✅ Pregătite {len(movies)} filme pentru Recombee")
    return movies


def prepare_ratings_for_recombee(ratings_df):
    """
    Pregătește ratingurile pentru încărcarea în Recombee.
    
    Returns:
        List de dicționare, fiecare reprezentând un rating/interacțiune
    """
    print("📦 Pregătire ratings pentru Recombee...")
    
    interactions = []
    for _, row in tqdm(ratings_df.iterrows(), total=len(ratings_df), desc="Procesare ratings"):
        interaction = {
            'user_id': str(row['userId']),
            'item_id': str(row['movieId']),
            'rating': float(row['rating']),
            'timestamp': int(row['timestamp'])
        }
        interactions.append(interaction)
    
    print(f"✅ Pregătite {len(interactions):,} interacțiuni pentru Recombee")
    return interactions


def get_popular_movies(movies_df, n=20):
    """
    Returnează cele mai populare filme (pentru Cold Start).
    
    Populare = vote_count * vote_average (formula ponderată)
    """
    df = movies_df.copy()
    
    # Calculăm scorul de popularitate
    # Folosim o medie ponderată: trebuie să aibă și multe voturi și un rating bun
    min_votes = df['vote_count'].quantile(0.75)  # Cel puțin 75% quantile de voturi
    df = df[df['vote_count'] >= min_votes]
    
    df['popularity_score'] = df['vote_count'] * df['vote_average']
    df = df.sort_values('popularity_score', ascending=False)
    
    return df.head(n)


def get_movies_by_genre(movies_df, genre):
    """
    Returnează filme filtrate după gen.
    """
    return movies_df[movies_df['genre_names'].apply(lambda x: genre in x if isinstance(x, list) else False)]


if __name__ == '__main__':
    # Test de încărcare date
    print("=" * 50)
    print("TEST: Încărcare și procesare date")
    print("=" * 50)
    
    try:
        movies = load_movies_metadata()
        print(f"\nPrimele 5 filme:\n{movies[['id', 'title', 'genres_str']].head()}")
        
        popular = get_popular_movies(movies)
        print(f"\nTop 5 filme populare:\n{popular[['title', 'vote_average', 'vote_count']].head()}")
    except FileNotFoundError as e:
        print(f"⚠️ Fișierele de date nu au fost găsite: {e}")
        print("📥 Descarcă dataset-ul de la: https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset")

