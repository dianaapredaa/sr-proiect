"""
Recombee Client Module - Integrare cu API-ul Recombee pentru recomandări
"""
from recombee_api_client.api_client import RecombeeClient
from recombee_api_client.api_requests import (
    AddItemProperty, SetItemValues, AddDetailView, AddRating, AddPurchase,
    RecommendItemsToUser, RecommendItemsToItem, RecommendNextItems,
    AddUser, SetUserValues, MergeUsers, DeleteUser,
    Batch, ResetDatabase, ListItems, ListUsers
)
from recombee_api_client.exceptions import APIException
from tqdm import tqdm
import config


class MovieRecommender:
    """
    Client pentru sistemul de recomandare filme folosind Recombee.
    
    Implementează o abordare hibridă:
    - Filtrare Colaborativă (bazată pe similaritatea utilizatorilor/filmelor)
    - Filtrare Bazată pe Conținut (bazată pe metadate: gen, regizor, actori, keywords)
    """
    
    def __init__(self, database_id=None, private_token=None, region=None):
        """
        Inițializează clientul Recombee.
        
        Args:
            database_id: ID-ul bazei de date Recombee
            private_token: Token-ul privat pentru autentificare
            region: Regiunea serverului ('eu-west', 'us-west', 'ap-se')
        """
        self.database_id = database_id or config.RECOMBEE_DATABASE_ID
        self.private_token = private_token or config.RECOMBEE_PRIVATE_TOKEN
        self.region = region or config.RECOMBEE_REGION
        
        # Construim URL-ul în funcție de regiune
        if self.region == 'eu-west':
            base_uri = 'https://rapi-eu-west.recombee.com'
        elif self.region == 'us-west':
            base_uri = 'https://rapi-us-west.recombee.com'
        elif self.region == 'ap-se':
            base_uri = 'https://rapi-ap-se.recombee.com'
        else:
            base_uri = None  # Default
        
        self.client = RecombeeClient(
            self.database_id, 
            self.private_token,
            base_uri=base_uri
        )
        
        print(f"✅ Client Recombee inițializat pentru database: {self.database_id}")
    
    def setup_item_properties(self):
        """
        Configurează proprietățile pentru item-uri (filme).
        Trebuie rulat o singură dată la setup-ul inițial.
        """
        print("⚙️ Configurare proprietăți pentru filme...")
        
        properties = [
            ('title', 'string'),
            ('overview', 'string'),
            ('genres', 'set'),
            ('keywords', 'set'),
            ('director', 'string'),
            ('actors', 'set'),
            ('release_date', 'string'),
            ('vote_average', 'double'),
            ('vote_count', 'int'),
            ('runtime', 'int'),
            ('poster_path', 'string'),
        ]
        
        requests = []
        for prop_name, prop_type in properties:
            requests.append(AddItemProperty(prop_name, prop_type))
        
        try:
            # Trimitem toate request-urile în batch
            self.client.send(Batch(requests))
            print(f"✅ Configurate {len(properties)} proprietăți pentru filme")
        except APIException as e:
            if 'already exists' in str(e).lower():
                print("ℹ️ Proprietățile există deja")
            else:
                raise
    
    def setup_user_properties(self):
        """
        Configurează proprietățile pentru utilizatori.
        """
        print("⚙️ Configurare proprietăți pentru utilizatori...")
        
        properties = [
            ('preferred_genres', 'set'),
            ('preferred_directors', 'set'),
            ('registration_date', 'timestamp'),
        ]
        
        requests = []
        for prop_name, prop_type in properties:
            from recombee_api_client.api_requests import AddUserProperty
            requests.append(AddUserProperty(prop_name, prop_type))
        
        try:
            self.client.send(Batch(requests))
            print(f"✅ Configurate {len(properties)} proprietăți pentru utilizatori")
        except APIException as e:
            if 'already exists' in str(e).lower():
                print("ℹ️ Proprietățile există deja")
            else:
                raise
    
    def add_movie(self, movie_data):
        """
        Adaugă un film în catalogul Recombee.
        
        Args:
            movie_data: Dict cu datele filmului
        """
        item_id = movie_data['item_id']
        
        # Pregătim valorile pentru Recombee
        values = {
            'title': movie_data.get('title', ''),
            'overview': movie_data.get('overview', ''),
            'genres': movie_data.get('genres', []),
            'keywords': movie_data.get('keywords', []),
            'director': movie_data.get('director', ''),
            'actors': movie_data.get('actors', []),
            'release_date': movie_data.get('release_date', ''),
            'vote_average': movie_data.get('vote_average', 0.0),
            'vote_count': movie_data.get('vote_count', 0),
            'runtime': movie_data.get('runtime', 0),
            'poster_path': movie_data.get('poster_path', ''),
        }
        
        # Setăm valorile (creează item-ul dacă nu există)
        self.client.send(SetItemValues(item_id, values, cascade_create=True))
    
    def add_movies_batch(self, movies_list, batch_size=1000):
        """
        Adaugă mai multe filme în batch pentru eficiență.
        
        Args:
            movies_list: Lista de dicționare cu datele filmelor
            batch_size: Dimensiunea batch-ului
        """
        print(f"📤 Încărcare {len(movies_list)} filme în Recombee...")
        
        for i in tqdm(range(0, len(movies_list), batch_size), desc="Încărcare filme"):
            batch_movies = movies_list[i:i+batch_size]
            requests = []
            
            for movie in batch_movies:
                values = {
                    'title': movie.get('title', ''),
                    'overview': movie.get('overview', ''),
                    'genres': movie.get('genres', []),
                    'keywords': movie.get('keywords', []),
                    'director': movie.get('director', ''),
                    'actors': movie.get('actors', []),
                    'release_date': movie.get('release_date', ''),
                    'vote_average': movie.get('vote_average', 0.0),
                    'vote_count': movie.get('vote_count', 0),
                    'runtime': movie.get('runtime', 0),
                    'poster_path': movie.get('poster_path', ''),
                }
                requests.append(SetItemValues(movie['item_id'], values, cascade_create=True))
            
            try:
                self.client.send(Batch(requests))
            except APIException as e:
                print(f"⚠️ Eroare la batch {i//batch_size}: {e}")
        
        print(f"✅ Încărcate {len(movies_list)} filme în Recombee")
    
    def add_rating(self, user_id, movie_id, rating, timestamp=None):
        """
        Adaugă un rating de la un utilizator pentru un film.
        
        Aceasta este interacțiunea principală folosită pentru filtrarea colaborativă.
        
        Args:
            user_id: ID-ul utilizatorului
            movie_id: ID-ul filmului
            rating: Rating-ul (1-5)
            timestamp: Unix timestamp (opțional)
        """
        # Normalizăm rating-ul la scala Recombee (-1 la 1)
        normalized_rating = (float(rating) - 3) / 2  # Convertim din 1-5 la -1 la 1
        
        self.client.send(AddRating(
            str(user_id), 
            str(movie_id), 
            normalized_rating,
            timestamp=timestamp,
            cascade_create=True
        ))
    
    def add_ratings_batch(self, ratings_list, batch_size=1000):
        """
        Adaugă mai multe rating-uri în batch.
        
        Args:
            ratings_list: Lista de dicționare cu rating-urile
            batch_size: Dimensiunea batch-ului
        """
        print(f"📤 Încărcare {len(ratings_list):,} rating-uri în Recombee...")
        
        for i in tqdm(range(0, len(ratings_list), batch_size), desc="Încărcare ratings"):
            batch_ratings = ratings_list[i:i+batch_size]
            requests = []
            
            for interaction in batch_ratings:
                normalized_rating = (float(interaction['rating']) - 3) / 2
                requests.append(AddRating(
                    str(interaction['user_id']),
                    str(interaction['item_id']),
                    normalized_rating,
                    timestamp=interaction.get('timestamp'),
                    cascade_create=True
                ))
            
            try:
                self.client.send(Batch(requests))
            except APIException as e:
                print(f"⚠️ Eroare la batch {i//batch_size}: {e}")
        
        print(f"✅ Încărcate {len(ratings_list):,} rating-uri în Recombee")
    
    def add_view(self, user_id, movie_id, timestamp=None):
        """
        Înregistrează că un utilizator a vizualizat detaliile unui film.
        """
        self.client.send(AddDetailView(
            str(user_id),
            str(movie_id),
            timestamp=timestamp,
            cascade_create=True
        ))
    
    def create_user(self, user_id, preferred_genres=None, preferred_directors=None):
        """
        Creează un utilizator nou cu preferințele inițiale.
        Util pentru rezolvarea problemei Cold Start.
        
        Args:
            user_id: ID-ul utilizatorului
            preferred_genres: Lista de genuri preferate
            preferred_directors: Lista de regizori preferați
        """
        values = {}
        if preferred_genres:
            values['preferred_genres'] = preferred_genres
        if preferred_directors:
            values['preferred_directors'] = preferred_directors
        
        self.client.send(SetUserValues(str(user_id), values, cascade_create=True))
        print(f"✅ Utilizator {user_id} creat cu succes")
    
    def get_recommendations_for_user(self, user_id, count=10, filter_genres=None, 
                                     exclude_watched=True, diversity=0.3):
        """
        Obține recomandări personalizate pentru un utilizator.
        
        Folosește abordarea HIBRIDĂ:
        - Filtrare Colaborativă: bazată pe rating-urile utilizatorilor similari
        - Filtrare pe Conținut: bazată pe genuri, keywords, regizor
        
        Args:
            user_id: ID-ul utilizatorului
            count: Numărul de recomandări
            filter_genres: Filtrează doar anumite genuri (opțional)
            exclude_watched: Exclude filmele deja vizionate/rătate
            diversity: Factor de diversitate (0-1)
            
        Returns:
            Lista de recomandări cu detalii despre filme
        """
        # Construim filtrul ReQL pentru genuri
        filter_expression = None
        if filter_genres:
            # Filtrăm după genuri specifice
            genre_filters = [f"'{g}' in 'genres'" for g in filter_genres]
            filter_expression = ' or '.join(genre_filters)
        
        # Booster pentru filme cu rating-uri bune
        booster = "'vote_average' > 7"
        
        try:
            response = self.client.send(RecommendItemsToUser(
                str(user_id),
                count,
                filter=filter_expression,
                booster=booster,
                cascade_create=True,
                return_properties=True,
                diversity=diversity,
                # Acest parametru activează logica hibridă în Recombee
                scenario='homepage',
                logic={
                    'name': 'recombee:hybrid',  # Folosește modelul hibrid
                }
            ))
            
            return self._format_recommendations(response['recomms'])
            
        except APIException as e:
            print(f"⚠️ Eroare la obținerea recomandărilor: {e}")
            return []
    
    def get_recommendations_for_new_user(self, preferred_genres, count=10):
        """
        Obține recomandări pentru un utilizator NOU (Cold Start - User).
        
        Folosește EXCLUSIV filtrarea bazată pe conținut deoarece
        nu avem istoric de interacțiuni pentru acest utilizator.
        
        Args:
            preferred_genres: Lista de genuri preferate (selectate la înregistrare)
            count: Numărul de recomandări
            
        Returns:
            Lista de recomandări bazate pe conținut
        """
        # Pentru utilizatori noi, creăm un filtru bazat pe genurile preferate
        if preferred_genres:
            genre_filters = [f"'{g}' in 'genres'" for g in preferred_genres]
            filter_expression = ' or '.join(genre_filters)
        else:
            filter_expression = None
        
        # Booster pentru filme populare și bine cotate
        # Aceasta este strategia pentru Cold Start
        booster = "'vote_average' * (if 'vote_count' > 1000 then 1.5 else 1)"
        
        try:
            # Folosim RecommendItemsToUser cu un user temporar
            temp_user_id = 'cold_start_temp'
            
            response = self.client.send(RecommendItemsToUser(
                temp_user_id,
                count,
                filter=filter_expression,
                booster=booster,
                cascade_create=True,
                return_properties=True,
                scenario='cold_start',
                logic={
                    'name': 'recombee:content-based',  # Doar filtrare pe conținut
                }
            ))
            
            return self._format_recommendations(response['recomms'])
            
        except APIException as e:
            print(f"⚠️ Eroare la recomandări cold start: {e}")
            return []
    
    def get_similar_movies(self, movie_id, count=10):
        """
        Găsește filme similare cu un film dat (Item-Based Collaborative Filtering).
        
        Util și pentru Cold Start - Item: când un film nou este adăugat,
        putem găsi filme similare bazat pe conținut.
        
        Args:
            movie_id: ID-ul filmului
            count: Numărul de filme similare
            
        Returns:
            Lista de filme similare
        """
        try:
            response = self.client.send(RecommendItemsToItem(
                str(movie_id),
                'similar_movies',  # Scenario pentru filme similare
                count,
                return_properties=True,
                cascade_create=True,
                logic={
                    'name': 'recombee:hybrid',
                }
            ))
            
            return self._format_recommendations(response['recomms'])
            
        except APIException as e:
            print(f"⚠️ Eroare la găsirea filmelor similare: {e}")
            return []
    
    def _format_recommendations(self, recomms):
        """
        Formatează recomandările într-un format util pentru aplicație.
        """
        formatted = []
        for rec in recomms:
            movie = {
                'id': rec['id'],
                'title': rec['values'].get('title', 'Unknown'),
                'overview': rec['values'].get('overview', ''),
                'genres': rec['values'].get('genres', []),
                'director': rec['values'].get('director', ''),
                'actors': rec['values'].get('actors', []),
                'vote_average': rec['values'].get('vote_average', 0),
                'vote_count': rec['values'].get('vote_count', 0),
                'runtime': rec['values'].get('runtime', 0),
                'poster_path': rec['values'].get('poster_path', ''),
                'release_date': rec['values'].get('release_date', ''),
            }
            formatted.append(movie)
        
        return formatted
    
    def reset_database(self):
        """
        Resetează baza de date Recombee.
        ATENȚIE: Șterge toate datele!
        """
        confirm = input("⚠️ Sigur vrei să resetezi baza de date? (yes/no): ")
        if confirm.lower() == 'yes':
            self.client.send(ResetDatabase())
            print("🗑️ Baza de date a fost resetată")
        else:
            print("❌ Resetare anulată")
    
    def get_stats(self):
        """
        Obține statistici despre baza de date.
        """
        try:
            items = self.client.send(ListItems())
            users = self.client.send(ListUsers())
            
            return {
                'total_items': len(items),
                'total_users': len(users)
            }
        except APIException as e:
            print(f"⚠️ Eroare la obținerea statisticilor: {e}")
            return {'total_items': 0, 'total_users': 0}


# Funcție helper pentru inițializarea rapidă
def init_recommender():
    """
    Inițializează și configurează sistemul de recomandare.
    """
    recommender = MovieRecommender()
    recommender.setup_item_properties()
    recommender.setup_user_properties()
    return recommender


if __name__ == '__main__':
    print("=" * 50)
    print("TEST: Recombee Client")
    print("=" * 50)
    
    # Verificăm dacă avem credențiale configurate
    if config.RECOMBEE_DATABASE_ID == 'your-database-id':
        print("⚠️ Configurează credențialele Recombee în .env sau config.py")
        print("📝 Creează un cont gratuit pe https://www.recombee.com/")
    else:
        recommender = init_recommender()
        stats = recommender.get_stats()
        print(f"\n📊 Statistici: {stats}")

