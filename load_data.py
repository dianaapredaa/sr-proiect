#!/usr/bin/env python3
"""
Script pentru încărcarea datelor în Recombee

Acest script:
1. Încarcă datele din fișierele CSV (Movies Dataset de pe Kaggle)
2. Procesează și combină datele
3. Le încarcă în baza de date Recombee pentru a fi folosite de sistemul de recomandare

Pași pentru utilizare:
1. Descarcă dataset-ul de la: https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset
2. Extrage fișierele în directorul 'data/'
3. Configurează credențialele Recombee în .env
4. Rulează acest script: python load_data.py
"""

import os
import sys
import argparse
from datetime import datetime

# Import local modules
from data_loader import (
    load_movies_metadata, 
    load_keywords, 
    load_credits, 
    load_ratings,
    merge_movie_data,
    prepare_movies_for_recombee,
    prepare_ratings_for_recombee
)
from recombee_client import MovieRecommender
import config


def check_data_files():
    """Verifică dacă fișierele de date există."""
    files = [
        config.MOVIES_METADATA_PATH,
        config.KEYWORDS_PATH,
        config.RATINGS_PATH
    ]
    
    missing = []
    for f in files:
        if not os.path.exists(f):
            missing.append(f)
    
    if missing:
        print("❌ Fișierele de date lipsesc:")
        for f in missing:
            print(f"   - {f}")
        print("\n📥 Descarcă dataset-ul de la:")
        print("   https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset")
        print(f"\n📁 Extrage fișierele în directorul '{config.DATA_DIR}/'")
        return False
    
    print("✅ Toate fișierele de date sunt prezente")
    return True


def check_recombee_config():
    """Verifică configurația Recombee."""
    if config.RECOMBEE_DATABASE_ID == 'your-database-id':
        print("❌ Credențialele Recombee nu sunt configurate!")
        print("\n📝 Pași pentru configurare:")
        print("   1. Creează un cont pe https://www.recombee.com/")
        print("   2. Creează o bază de date nouă")
        print("   3. Copiază env.example în .env")
        print("   4. Completează RECOMBEE_DATABASE_ID și RECOMBEE_PRIVATE_TOKEN")
        return False
    
    print("✅ Credențialele Recombee sunt configurate")
    return True


def load_movies_to_recombee(recommender, limit=None):
    """Încarcă filmele în Recombee."""
    print("\n" + "=" * 50)
    print("📚 ÎNCĂRCARE FILME ÎN RECOMBEE")
    print("=" * 50)
    
    # Încarcă datele
    movies = load_movies_metadata()
    
    # Opțional: încarcă keywords și credits
    keywords = None
    credits = None
    
    if os.path.exists(config.KEYWORDS_PATH):
        keywords = load_keywords()
    
    if os.path.exists(config.CREDITS_PATH):
        credits = load_credits()
    
    # Combină datele
    movies_full = merge_movie_data(movies, keywords, credits)
    
    # Limitează dacă este specificat
    if limit:
        movies_full = movies_full.head(limit)
        print(f"⚠️ Limitare la {limit} filme pentru test")
    
    # Pregătește pentru Recombee
    movies_data = prepare_movies_for_recombee(movies_full)
    
    # Configurează proprietățile
    recommender.setup_item_properties()
    
    # Încarcă filmele
    recommender.add_movies_batch(movies_data, batch_size=500)
    
    return len(movies_data)


def load_ratings_to_recombee(recommender, limit=None):
    """Încarcă rating-urile în Recombee."""
    print("\n" + "=" * 50)
    print("⭐ ÎNCĂRCARE RATING-URI ÎN RECOMBEE")
    print("=" * 50)
    
    # Încarcă rating-urile (cu sample dacă specificat)
    ratings = load_ratings(sample_size=limit)
    
    # Pregătește pentru Recombee
    ratings_data = prepare_ratings_for_recombee(ratings)
    
    # Configurează proprietățile utilizatorilor
    recommender.setup_user_properties()
    
    # Încarcă rating-urile
    recommender.add_ratings_batch(ratings_data, batch_size=1000)
    
    # Calculează preferințele utilizatorilor din rating-uri
    # SKIP: Calcularea preferințelor e prea lentă (multe API calls)
    # Recombee va folosi automat rating-urile pentru recomandări
    print("\n" + "=" * 50)
    print("✅ RATING-URI ÎNCĂRCATE CU SUCCES")
    print("=" * 50)
    print("ℹ️  Recombee va folosi automat rating-urile pentru recomandări hibride")
    print("   (Nu e nevoie să calculăm manual preferințele)")
    
    return len(ratings_data)


def main():
    parser = argparse.ArgumentParser(
        description='Încarcă datele în Recombee pentru sistemul de recomandare filme'
    )
    parser.add_argument(
        '--movies-only', 
        action='store_true',
        help='Încarcă doar filmele, fără rating-uri'
    )
    parser.add_argument(
        '--ratings-only',
        action='store_true', 
        help='Încarcă doar rating-urile'
    )
    parser.add_argument(
        '--limit-movies',
        type=int,
        default=None,
        help='Limitează numărul de filme (pentru test)'
    )
    parser.add_argument(
        '--limit-ratings',
        type=int,
        default=None,
        help='Limitează numărul de rating-uri (pentru test)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Mod test: încarcă doar 100 filme și 1000 rating-uri'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Resetează baza de date Recombee înainte de încărcare (șterge toate datele existente!)'
    )
    
    args = parser.parse_args()
    
    # Header
    print("\n" + "=" * 60)
    print("🎬 SISTEM DE RECOMANDARE FILME - ÎNCĂRCARE DATE")
    print("=" * 60)
    print(f"⏰ Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificări
    if not check_data_files():
        sys.exit(1)
    
    if not check_recombee_config():
        sys.exit(1)
    
    # Configurare limite pentru mod test
    movies_limit = args.limit_movies
    ratings_limit = args.limit_ratings
    
    if args.test:
        movies_limit = movies_limit or 100
        ratings_limit = ratings_limit or 1000
        print(f"\n🧪 Mod test activat: {movies_limit} filme, {ratings_limit} rating-uri")
    
    # Inițializare client Recombee
    try:
        recommender = MovieRecommender()
    except Exception as e:
        print(f"❌ Eroare la conectarea cu Recombee: {e}")
        sys.exit(1)
    
    # Resetare baza de date dacă este solicitat
    if args.reset:
        print("\n" + "=" * 60)
        print("🗑️  RESETARE BAZĂ DE DATE RECOMBEE")
        print("=" * 60)
        print("⚠️  ATENȚIE: Toate datele existente vor fi șterse!")
        if recommender.reset_database(skip_confirmation=True):
            print("✅ Baza de date a fost resetată cu succes")
        else:
            print("❌ Eroare la resetare. Continuăm cu datele existente...")
    
    # Încărcare date
    total_movies = 0
    total_ratings = 0
    
    try:
        if not args.ratings_only:
            total_movies = load_movies_to_recombee(recommender, limit=movies_limit)
        
        if not args.movies_only:
            total_ratings = load_ratings_to_recombee(recommender, limit=ratings_limit)
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Încărcare întreruptă de utilizator")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Eroare în timpul încărcării: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Rezumat
    print("\n" + "=" * 60)
    print("✅ ÎNCĂRCARE COMPLETĂ!")
    print("=" * 60)
    print(f"📽️  Filme încărcate: {total_movies:,}")
    print(f"⭐ Rating-uri încărcate: {total_ratings:,}")
    print(f"⏰ Final: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Afișează statistici Recombee
    stats = recommender.get_stats()
    print(f"\n📊 Statistici Recombee:")
    print(f"   - Total filme în DB: {stats['total_items']:,}")
    print(f"   - Total utilizatori: {stats['total_users']:,}")
    
    # Verifică calitatea datelor
    print("\n" + "=" * 60)
    recommender.verify_data_quality(sample_size=5)
    
    print("\n🚀 Pornește aplicația cu: python app.py")


if __name__ == '__main__':
    main()

