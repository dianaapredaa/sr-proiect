"""
Recombee Client Module - Integrare cu API-ul Recombee pentru recomandări
"""
from recombee_api_client.api_client import RecombeeClient, Region
from recombee_api_client.api_requests import (
    AddItemProperty, SetItemValues, AddDetailView, AddRating, AddPurchase,
    RecommendItemsToUser, RecommendItemsToItem, RecommendNextItems,
    AddUser, SetUserValues, MergeUsers, DeleteUser,
    Batch, ResetDatabase, ListItems, ListUsers, GetItemValues, GetUserValues,
    ListUserRatings
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
        self.region_str = region or config.RECOMBEE_REGION
        
        # Mapăm string-ul regiunii la enum Region
        region_map = {
            'eu-west': Region.EU_WEST,
            'us-west': Region.US_WEST,
            'ap-se': Region.AP_SE,
            'ca-east': Region.CA_EAST,
        }
        
        self.region = region_map.get(self.region_str.lower(), Region.EU_WEST)
        
        # Inițializăm clientul Recombee cu regiunea corectă
        self.client = RecombeeClient(
            self.database_id, 
            self.private_token,
            region=self.region
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
        
        # Pregătim valorile pentru Recombee - asigurăm tipurile corecte
        values = {
            'title': str(movie_data.get('title', '')),
            'overview': str(movie_data.get('overview', '')),
            'genres': movie_data.get('genres', []) if isinstance(movie_data.get('genres'), list) else [],
            'keywords': movie_data.get('keywords', []) if isinstance(movie_data.get('keywords'), list) else [],
            'director': str(movie_data.get('director', '')),
            'actors': movie_data.get('actors', []) if isinstance(movie_data.get('actors'), list) else [],
            'release_date': str(movie_data.get('release_date', '')),
            'vote_average': float(movie_data.get('vote_average', 0.0)),
            'vote_count': int(movie_data.get('vote_count', 0)),
            'runtime': int(movie_data.get('runtime', 0)),
            'poster_path': str(movie_data.get('poster_path', '')),
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
                # Asigurăm că toate valorile sunt în formatul corect
                values = {
                    'title': str(movie.get('title', '')),
                    'overview': str(movie.get('overview', '')),
                    'genres': movie.get('genres', []) if isinstance(movie.get('genres'), list) else [],
                    'keywords': movie.get('keywords', []) if isinstance(movie.get('keywords'), list) else [],
                    'director': str(movie.get('director', '')),
                    'actors': movie.get('actors', []) if isinstance(movie.get('actors'), list) else [],
                    'release_date': str(movie.get('release_date', '')),
                    'vote_average': float(movie.get('vote_average', 0.0)),
                    'vote_count': int(movie.get('vote_count', 0)),
                    'runtime': int(movie.get('runtime', 0)),
                    'poster_path': str(movie.get('poster_path', '')),
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
        Creează automat utilizatorii cu proprietăți default dacă nu există.
        
        Args:
            ratings_list: Lista de dicționare cu rating-urile
            batch_size: Dimensiunea batch-ului
        """
        print(f"📤 Încărcare {len(ratings_list):,} rating-uri în Recombee...")
        
        # Colectăm toți utilizatorii unici pentru a le seta proprietăți default
        unique_users = set()
        for interaction in ratings_list:
            unique_users.add(str(interaction['user_id']))
        
        print(f"👥 Creare {len(unique_users):,} utilizatori cu proprietăți default...")
        
        # Creăm utilizatorii cu proprietăți default în batch-uri
        user_batch_size = 1000
        for i in tqdm(range(0, len(unique_users), user_batch_size), desc="Creare utilizatori"):
            user_batch = list(unique_users)[i:i+user_batch_size]
            user_requests = []
            
            for user_id in user_batch:
                # Setăm proprietăți default pentru fiecare utilizator
                user_requests.append(SetUserValues(
                    user_id,
                    {
                        'preferred_genres': [],  # Listă goală (nu null)
                        'preferred_directors': [],  # Listă goală (nu null)
                    },
                    cascade_create=True
                ))
            
            try:
                self.client.send(Batch(user_requests))
            except APIException as e:
                print(f"⚠️ Eroare la crearea utilizatorilor batch {i//user_batch_size}: {e}")
        
        # Acum încărcăm rating-urile
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
                    cascade_create=False  # Utilizatorii sunt deja creați
                ))
            
            try:
                self.client.send(Batch(requests))
            except APIException as e:
                print(f"⚠️ Eroare la batch {i//batch_size}: {e}")
        
        print(f"✅ Încărcate {len(ratings_list):,} rating-uri în Recombee")
    
    def calculate_user_preferences_from_ratings(self, user_id, min_rating=3.5):
        """
        Calculează preferințele utilizatorului bazate pe rating-urile date.
        Extrage genurile și regizorii din filmele apreciate (rating >= min_rating).
        
        Args:
            user_id: ID-ul utilizatorului
            min_rating: Rating minim pentru a considera un film apreciat (default: 3.5)
        """
        try:
            # Obținem toate rating-urile utilizatorului
            ratings = self.client.send(ListUserRatings(str(user_id)))
            
            if not ratings:
                return  # Utilizatorul nu are rating-uri
            
            # Colectăm genurile și regizorii din filmele apreciate
            preferred_genres = {}
            preferred_directors = {}
            
            for rating_data in ratings:
                # Rating-ul în Recombee este normalizat (-1 la 1), convertim înapoi
                # rating_data este un dict cu 'itemId' și 'rating'
                rating_value = rating_data.get('rating', 0)
                rating = (rating_value * 2) + 3  # Convertim din -1..1 la 1..5
                
                if rating >= min_rating:
                    item_id = rating_data.get('itemId')
                    if item_id:
                        try:
                            # Obținem datele filmului
                            item = self.client.send(GetItemValues(str(item_id)))
                            
                            # Adăugăm genurile
                            genres = item.get('genres', [])
                            if isinstance(genres, list):
                                for genre in genres:
                                    preferred_genres[genre] = preferred_genres.get(genre, 0) + 1
                            
                            # Adăugăm regizorul
                            director = item.get('director', '')
                            if director and director != '':
                                preferred_directors[director] = preferred_directors.get(director, 0) + 1
                        except Exception as e:
                            # Ignorăm erorile pentru filme individuale
                            continue
            
            # Sortăm și luăm top genuri și regizori
            top_genres = sorted(preferred_genres.items(), key=lambda x: x[1], reverse=True)[:10]
            top_directors = sorted(preferred_directors.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Actualizăm preferințele utilizatorului
            user_values = {
                'preferred_genres': [genre for genre, _ in top_genres] if top_genres else [],
                'preferred_directors': [director for director, _ in top_directors] if top_directors else [],
            }
            
            self.client.send(SetUserValues(str(user_id), user_values))
            
        except APIException as e:
            # Ignorăm erorile pentru utilizatori individuali
            pass
    
    def update_all_users_preferences(self, batch_size=100):
        """
        Actualizează preferințele pentru toți utilizatorii bazate pe rating-urile lor.
        """
        print("\n" + "=" * 60)
        print("🎯 CALCULARE PREFERINȚE UTILIZATORI")
        print("=" * 60)
        
        try:
            # Obținem toți utilizatorii
            users = self.client.send(ListUsers())
            print(f"👥 Calculare preferințe pentru {len(users)} utilizatori...")
            
            for i in tqdm(range(0, len(users), batch_size), desc="Actualizare preferințe"):
                user_batch = users[i:i+batch_size]
                for user_id in user_batch:
                    self.calculate_user_preferences_from_ratings(user_id)
            
            print("✅ Preferințe actualizate pentru toți utilizatorii")
            
        except APIException as e:
            print(f"⚠️ Eroare la actualizarea preferințelor: {e}")
    
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
        # ATENȚIE: Ghilimele simple (') sunt pentru proprietăți, ghilimele duble (") pentru string-uri constante
        filter_expression = None
        if filter_genres:
            # Filtrăm după genuri specifice
            # Format corect: "Animation" in 'genres' (ghilimele duble pentru string, simple pentru proprietate)
            genre_filters = [f'"{g}" in \'genres\'' for g in filter_genres]
            filter_expression = ' or '.join(genre_filters)
        
        # Booster pentru filme cu rating-uri bune (returnează număr, nu boolean)
        # Multiplică scorul cu 1.5 pentru filme cu rating > 7, altfel 1.0
        # booster = "if 'vote_average' > 7 then 1.5 else 1.0"
        booster = """
        if 'vote_count' < 500 AND 'vote_average' > 7 then 1.3 
        else if 'vote_average' > 7 then 1.5 
        else 1.0
        """
        
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
                    'name': 'recombee:personal',  # Recomandări personalizate (hibrid implicit)
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
        # ATENȚIE: Ghilimele simple (') sunt pentru proprietăți, ghilimele duble (") pentru string-uri constante
        if preferred_genres:
            genre_filters = [f'"{g}" in \'genres\'' for g in preferred_genres]
            filter_expression = ' or '.join(genre_filters)
        else:
            filter_expression = None
        
        # Booster pentru filme populare și bine cotate
        # Aceasta este strategia pentru Cold Start
        # Returnează un număr care multiplică scorul
        booster = "if 'vote_count' > 1000 AND 'vote_average' > 7 then 1.5 else if 'vote_average' > 7 then 1.2 else 1.0"
        
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
                    'name': 'recombee:personal',  # Recomandări personalizate bazate pe conținut
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
                    'name': 'recombee:similar',  # Logic valid pentru item-to-item recommendations
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
    
    def reset_database(self, skip_confirmation=False):
        """
        Resetează baza de date Recombee.
        ATENȚIE: Șterge toate datele!
        
        Args:
            skip_confirmation: Dacă True, nu cere confirmare (util pentru script-uri)
        """
        if not skip_confirmation:
            confirm = input("⚠️ Sigur vrei să resetezi baza de date? (yes/no): ")
            if confirm.lower() != 'yes':
                print("❌ Resetare anulată")
                return False
        
        try:
            self.client.send(ResetDatabase())
            print("🗑️ Baza de date a fost resetată")
            return True
        except APIException as e:
            print(f"❌ Eroare la resetare: {e}")
            return False
    
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
    
    def verify_data_quality(self, sample_size=10):
        """
        Verifică calitatea datelor încărcate în Recombee.
        """
        from recombee_api_client.api_requests import GetItemValues, GetUserValues
        
        print("\n" + "=" * 60)
        print("🔍 VERIFICARE CALITATE DATE")
        print("=" * 60)
        
        try:
            # Verifică câteva filme (folosim count în loc de limit)
            items = self.client.send(ListItems(count=sample_size))
            print(f"\n📽️  Verificare {len(items)} filme (sample):")
            
            for item_id in items[:5]:
                try:
                    item = self.client.send(GetItemValues(item_id))
                    title = item.get('title', 'N/A')
                    genres = item.get('genres', [])
                    has_data = bool(title and title != '' and title != 'N/A')
                    print(f"   - {item_id}: title='{title[:50]}...' genres={len(genres)} has_data={has_data}")
                except Exception as e:
                    print(f"   - {item_id}: EROARE - {e}")
            
            # Verifică câțiva utilizatori (folosim count în loc de limit)
            users = self.client.send(ListUsers(count=sample_size))
            print(f"\n👥 Verificare {len(users)} utilizatori (sample):")
            
            for user_id in users[:5]:
                try:
                    user = self.client.send(GetUserValues(user_id))
                    preferred_genres = user.get('preferred_genres', [])
                    preferred_directors = user.get('preferred_directors', [])
                    registration_date = user.get('registration_date', None)
                    print(f"   - {user_id}: genres={len(preferred_genres)} directors={len(preferred_directors)} reg_date={registration_date}")
                except Exception as e:
                    print(f"   - {user_id}: EROARE - {e}")
            
            print("\n✅ Verificare completă")
            
        except APIException as e:
            print(f"❌ Eroare la verificare: {e}")


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

