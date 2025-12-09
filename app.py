"""
Movie Recommendation System - Flask Application
Sistem de Recomandare Filme cu abordare hibridă
"""
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import uuid
import os

import config
from recombee_client import MovieRecommender
from data_loader import (
    load_movies_metadata, load_keywords, load_credits,
    merge_movie_data, get_popular_movies, get_movies_by_genre
)

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Inițializare recommender (lazy loading)
recommender = None
movies_cache = None


def get_recommender():
    """Lazy loading pentru Recombee client."""
    global recommender
    if recommender is None:
        recommender = MovieRecommender()
    return recommender


def get_movies_cache():
    """Lazy loading pentru cache-ul de filme local."""
    global movies_cache
    if movies_cache is None:
        try:
            movies = load_movies_metadata()
            movies_cache = movies
        except FileNotFoundError:
            movies_cache = None
    return movies_cache


# ==================== ROUTES - Pages ====================

@app.route('/')
def index():
    """Pagina principală cu recomandări."""
    return render_template('index.html')


@app.route('/movie/<movie_id>')
def movie_details(movie_id):
    """Pagina de detalii pentru un film."""
    return render_template('movie.html', movie_id=movie_id)


@app.route('/register')
def register():
    """Pagina de înregistrare utilizator (Cold Start)."""
    return render_template('register.html', genres=config.GENRES_FOR_COLD_START)


# ==================== ROUTES - API ====================

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """
    API: Obține recomandări personalizate pentru utilizator.
    
    Query params:
        - user_id: ID-ul utilizatorului
        - count: Numărul de recomandări (default: 10)
        - genres: Filtrare după genuri (comma-separated)
    
    Folosește abordarea HIBRIDĂ:
    - Pentru utilizatori cu istoric: Filtrare Colaborativă + Conținut
    - Pentru utilizatori noi (Cold Start): Doar Filtrare pe Conținut
    """
    user_id = request.args.get('user_id', session.get('user_id'))
    count = int(request.args.get('count', config.DEFAULT_NUM_RECOMMENDATIONS))
    genres_param = request.args.get('genres', '')
    
    genres = [g.strip() for g in genres_param.split(',') if g.strip()] if genres_param else None
    
    # Verificăm dacă avem Recombee configurat
    if config.RECOMBEE_DATABASE_ID == 'your-database-id':
        # Mod demo - returnăm date din cache-ul local
        return get_demo_recommendations(count, genres)
    
    try:
        rec = get_recommender()
        
        if user_id:
            # Utilizator existent - recomandări hibride
            recommendations = rec.get_recommendations_for_user(
                user_id, 
                count=count, 
                filter_genres=genres
            )
        else:
            # Utilizator nou (Cold Start) - recomandări bazate pe conținut
            preferred_genres = genres or session.get('preferred_genres', [])
            recommendations = rec.get_recommendations_for_new_user(
                preferred_genres, 
                count=count
            )
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'method': 'hybrid' if user_id else 'content_based',
            'user_id': user_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'recommendations': []
        }), 500


@app.route('/api/similar/<movie_id>', methods=['GET'])
def get_similar_movies(movie_id):
    """
    API: Obține filme similare cu un film dat.
    Folosește Item-Based Collaborative Filtering.
    
    Util pentru:
    - Cold Start pentru filme noi
    - Secțiunea "Dacă ți-a plăcut X..."
    """
    count = int(request.args.get('count', 6))
    
    if config.RECOMBEE_DATABASE_ID == 'your-database-id':
        # Mod demo
        return get_demo_similar(movie_id, count)
    
    try:
        rec = get_recommender()
        similar = rec.get_similar_movies(movie_id, count=count)
        
        return jsonify({
            'success': True,
            'similar_movies': similar,
            'source_movie_id': movie_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'similar_movies': []
        }), 500


@app.route('/api/rate', methods=['POST'])
def rate_movie():
    """
    API: Înregistrează rating-ul unui utilizator pentru un film.
    Aceasta hrănește sistemul de Filtrare Colaborativă.
    """
    data = request.json
    user_id = data.get('user_id', session.get('user_id'))
    movie_id = data.get('movie_id')
    rating = data.get('rating')
    
    if not all([user_id, movie_id, rating]):
        return jsonify({
            'success': False,
            'error': 'Missing required fields: user_id, movie_id, rating'
        }), 400
    
    if config.RECOMBEE_DATABASE_ID == 'your-database-id':
        # Mod demo - doar salvăm în sesiune
        if 'ratings' not in session:
            session['ratings'] = {}
        session['ratings'][movie_id] = rating
        return jsonify({'success': True, 'demo_mode': True})
    
    try:
        rec = get_recommender()
        rec.add_rating(user_id, movie_id, rating)
        
        return jsonify({
            'success': True,
            'message': f'Rating {rating} înregistrat pentru filmul {movie_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/user/register', methods=['POST'])
def register_user():
    """
    API: Înregistrează un utilizator nou cu preferințele inițiale.
    Aceasta rezolvă problema de Cold Start pentru utilizatori noi.
    """
    data = request.json
    preferred_genres = data.get('preferred_genres', [])
    preferred_directors = data.get('preferred_directors', [])
    
    # Generăm un ID unic pentru utilizator
    user_id = str(uuid.uuid4())
    
    # Salvăm în sesiune
    session['user_id'] = user_id
    session['preferred_genres'] = preferred_genres
    
    if config.RECOMBEE_DATABASE_ID != 'your-database-id':
        try:
            rec = get_recommender()
            rec.create_user(user_id, preferred_genres, preferred_directors)
        except Exception as e:
            print(f"Warning: Nu s-a putut crea utilizatorul în Recombee: {e}")
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'message': 'Utilizator înregistrat cu succes'
    })


@app.route('/api/user/preferences', methods=['GET'])
def get_user_preferences():
    """API: Obține preferințele utilizatorului curent."""
    return jsonify({
        'user_id': session.get('user_id'),
        'preferred_genres': session.get('preferred_genres', []),
        'is_new_user': session.get('user_id') is None
    })


@app.route('/api/genres', methods=['GET'])
def get_genres():
    """API: Returnează lista de genuri disponibile."""
    return jsonify({
        'genres': config.GENRES_FOR_COLD_START
    })


@app.route('/api/popular', methods=['GET'])
def get_popular():
    """
    API: Returnează filme populare.
    Util pentru Cold Start și pagina principală.
    """
    count = int(request.args.get('count', config.POPULAR_MOVIES_COUNT))
    
    movies = get_movies_cache()
    if movies is None:
        return jsonify({
            'success': False,
            'error': 'Dataset not loaded',
            'movies': get_demo_popular_movies(count)
        })
    
    popular = get_popular_movies(movies, n=count)
    
    result = []
    for _, row in popular.iterrows():
        result.append({
            'id': str(row['id']),
            'title': row['title'],
            'overview': row.get('overview', '')[:200],
            'genres': row.get('genre_names', []),
            'vote_average': row.get('vote_average', 0),
            'vote_count': int(row.get('vote_count', 0)),
            'poster_path': row.get('poster_path', '')
        })
    
    return jsonify({
        'success': True,
        'movies': result
    })


@app.route('/api/movie/<movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    """API: Obține detaliile unui film."""
    movies = get_movies_cache()
    
    if movies is None:
        return jsonify({
            'success': False,
            'error': 'Dataset not loaded',
            'movie': get_demo_movie(movie_id)
        })
    
    movie = movies[movies['id'] == int(movie_id)]
    
    if movie.empty:
        return jsonify({
            'success': False,
            'error': 'Movie not found'
        }), 404
    
    row = movie.iloc[0]
    return jsonify({
        'success': True,
        'movie': {
            'id': str(row['id']),
            'title': row['title'],
            'overview': row.get('overview', ''),
            'genres': row.get('genre_names', []),
            'vote_average': row.get('vote_average', 0),
            'vote_count': int(row.get('vote_count', 0)),
            'runtime': int(row.get('runtime', 0)),
            'release_date': row.get('release_date', ''),
            'poster_path': row.get('poster_path', '')
        }
    })


# ==================== DEMO DATA ====================

def get_demo_popular_movies(count=10):
    """Returnează date demo pentru filme populare."""
    demo_movies = [
        {'id': '862', 'title': 'Toy Story', 'overview': 'A cowboy doll is profoundly threatened and jealous when a new spaceman figure supplants him as top toy in a boy\'s room.', 'genres': ['Animation', 'Comedy', 'Family'], 'vote_average': 7.7, 'vote_count': 5415, 'poster_path': '/rhIRbceoE9lR4veEXuwCC2wARtG.jpg'},
        {'id': '8844', 'title': 'Jumanji', 'overview': 'When siblings Judy and Peter discover an enchanted board game that opens the door to a magical world, they unwittingly invite Alan -- an adult who\'s been trapped inside the game for 26 years.', 'genres': ['Adventure', 'Fantasy', 'Family'], 'vote_average': 6.9, 'vote_count': 2413, 'poster_path': '/vgpXmVaVyUL920SAYtoH9B5xNsE.jpg'},
        {'id': '550', 'title': 'Fight Club', 'overview': 'An insomniac office worker looking for a way to change his life crosses paths with a devil-may-care soap maker.', 'genres': ['Drama'], 'vote_average': 8.4, 'vote_count': 9678, 'poster_path': '/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg'},
        {'id': '13', 'title': 'Forrest Gump', 'overview': 'A man with a low IQ has accomplished great things in his life and been present during significant historic events.', 'genres': ['Comedy', 'Drama', 'Romance'], 'vote_average': 8.5, 'vote_count': 8147, 'poster_path': '/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg'},
        {'id': '603', 'title': 'The Matrix', 'overview': 'Set in the 22nd century, The Matrix tells the story of a computer hacker who joins a group of underground insurgents fighting the vast and powerful computers who now rule the earth.', 'genres': ['Action', 'Science Fiction'], 'vote_average': 8.1, 'vote_count': 9079, 'poster_path': '/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg'},
        {'id': '157336', 'title': 'Interstellar', 'overview': 'The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel.', 'genres': ['Adventure', 'Drama', 'Science Fiction'], 'vote_average': 8.3, 'vote_count': 11187, 'poster_path': '/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg'},
        {'id': '27205', 'title': 'Inception', 'overview': 'Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious of his targets is offered a chance to regain his old life.', 'genres': ['Action', 'Science Fiction', 'Adventure'], 'vote_average': 8.3, 'vote_count': 13752, 'poster_path': '/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg'},
        {'id': '155', 'title': 'The Dark Knight', 'overview': 'Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and District Attorney Harvey Dent, Batman sets out to dismantle the remaining criminal organizations.', 'genres': ['Drama', 'Action', 'Crime', 'Thriller'], 'vote_average': 8.5, 'vote_count': 12269, 'poster_path': '/qJ2tW6WMUDux911r6m7haRef0WH.jpg'},
        {'id': '680', 'title': 'Pulp Fiction', 'overview': 'A burger-loving hit man, his philosophical partner, a drug-addled gangster\'s moll and a washed-up boxer converge in this sprawling, comedic crime caper.', 'genres': ['Thriller', 'Crime'], 'vote_average': 8.5, 'vote_count': 8428, 'poster_path': '/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg'},
        {'id': '238', 'title': 'The Godfather', 'overview': 'Spanning the years 1945 to 1955, a chronicle of the fictional Italian-American Corleone crime family.', 'genres': ['Drama', 'Crime'], 'vote_average': 8.7, 'vote_count': 6024, 'poster_path': '/3bhkrj58Vtu7enYsRolD1fZdja1.jpg'},
    ]
    return demo_movies[:count]


def get_demo_recommendations(count, genres=None):
    """Returnează recomandări demo."""
    movies = get_demo_popular_movies(count)
    if genres:
        movies = [m for m in movies if any(g in m['genres'] for g in genres)]
    
    return jsonify({
        'success': True,
        'recommendations': movies[:count],
        'method': 'demo',
        'demo_mode': True,
        'message': 'Running in demo mode - configure Recombee for full functionality'
    })


def get_demo_similar(movie_id, count):
    """Returnează filme similare demo."""
    movies = get_demo_popular_movies(count + 1)
    # Exclude filmul sursă și returnează restul
    similar = [m for m in movies if m['id'] != movie_id][:count]
    
    return jsonify({
        'success': True,
        'similar_movies': similar,
        'source_movie_id': movie_id,
        'demo_mode': True
    })


def get_demo_movie(movie_id):
    """Returnează detalii demo pentru un film."""
    movies = get_demo_popular_movies(20)
    for m in movies:
        if m['id'] == movie_id:
            return m
    return movies[0] if movies else None


# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("🎬 Movie Recommendation System")
    print("   Sistem de Recomandare Filme - Abordare Hibridă")
    print("=" * 60)
    
    if config.RECOMBEE_DATABASE_ID == 'your-database-id':
        print("\n⚠️  Running in DEMO MODE")
        print("   Configure Recombee credentials in .env for full functionality")
        print("   Visit https://www.recombee.com/ to create a free account\n")
    
    print(f"🌐 Starting server at http://{config.HOST}:{config.PORT}")
    app.run(
        host=config.HOST, 
        port=config.PORT, 
        debug=config.DEBUG
    )

