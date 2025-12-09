# 🎬 CineMatch - Prezentare Etapa II
## Sistem de Recomandare Filme

**Diana Preda & Omer Tarik - E-Guvernare**

---

# 1. FUNCȚIONALITATE SR (2 puncte)

## Tipul Sistemului de Recomandare: **HIBRID**

Sistemul CineMatch combină două abordări:

### A. Filtrare Colaborativă (Collaborative Filtering)
- **User-Based**: Găsește utilizatori cu gusturi similare
- **Item-Based**: Găsește filme cu pattern-uri de rating similare

### B. Filtrare Bazată pe Conținut (Content-Based Filtering)
- Analizează metadatele filmelor: gen, regizor, actori, keywords
- Potrivește atributele cu preferințele utilizatorului

---

## Pseudocod Algoritm Hibrid

```
ALGORITM RecomandareHibridă(utilizator_id, număr_recomandări):
    
    DACĂ utilizator_este_nou(utilizator_id):
        // COLD START - Folosim doar filtrare pe conținut
        preferințe = obține_preferințe_înregistrare(utilizator_id)
        recomandări = filtrare_conținut(preferințe)
    
    ALTFEL:
        // Utilizator existent - Abordare hibridă
        
        // Pas 1: Filtrare Colaborativă
        utilizatori_similari = găsește_vecini(utilizator_id, k=50)
        candidați_colaborativ = []
        PENTRU FIECARE vecin IN utilizatori_similari:
            filme_apreciate = obține_filme_rating_mare(vecin)
            candidați_colaborativ.adaugă(filme_apreciate)
        
        // Pas 2: Filtrare pe Conținut
        profil_utilizator = construiește_profil(utilizator_id)
        candidați_conținut = potrivește_atribute(profil_utilizator)
        
        // Pas 3: Combină scorurile (ponderare hibridă)
        PENTRU FIECARE film IN candidați:
            scor_colaborativ = calculează_scor_colaborativ(film)
            scor_conținut = calculează_scor_conținut(film)
            scor_final = α * scor_colaborativ + (1-α) * scor_conținut
            // α = 0.7 (favorizăm colaborativ când avem date)
        
        // Pas 4: Aplică diversitate
        recomandări = selectează_diverse(candidați, număr_recomandări)
    
    RETURNEAZĂ recomandări
```

---

## Implementare în Recombee

```python
# recombee_client.py - Metoda de recomandare hibridă

def get_recommendations_for_user(self, user_id, count=10, filter_genres=None):
    """
    Obține recomandări personalizate folosind abordarea hibridă.
    """
    response = self.client.send(RecommendItemsToUser(
        str(user_id),
        count,
        cascade_create=True,
        return_properties=True,
        diversity=0.3,  # Factor de diversitate
        scenario='homepage',
        logic={
            'name': 'recombee:hybrid',  # Activează modelul hibrid
        }
    ))
    return self._format_recommendations(response['recomms'])
```

---

# 2. DATASET (2 puncte)

## The Movies Dataset (Kaggle)

| Caracteristică | Valoare |
|---------------|---------|
| **Sursa** | Kaggle - The Movies Dataset |
| **Filme** | 45,466 filme |
| **Rating-uri** | 100,004 (sample) / 26M (complet) |
| **Utilizatori** | 671 (sample) / 270,000 (complet) |
| **Perioada** | 1874 - 2017 |

### Fișiere utilizate:

| Fișier | Coloane principale | Utilizare |
|--------|-------------------|-----------|
| `movies_metadata.csv` | id, title, genres, overview, vote_average | Catalog filme |
| `keywords.csv` | id, keywords | Filtrare conținut |
| `credits.csv` | id, cast, crew | Actori, regizori |
| `ratings_small.csv` | userId, movieId, rating, timestamp | Interacțiuni |

---

## Exemple Particulare din Dataset

### Exemplul 1: Film cu OVERVIEW FOARTE SCURT vs LUNG

**🔴 Film cu descriere SCURTĂ (52 caractere):**
```
ID: 21032
Titlu: "Balto"
Overview: "An outcast half-wolf risks his life to prevent a deadly epidemic..."
Lungime: 96 caractere

PROBLEMĂ: Filtrarea pe conținut are puțin text pentru analiză.
SOLUȚIE: Folosim keywords și genres pentru a compensa.
```

**🟢 Film cu descriere LUNGĂ (892 caractere):**
```
ID: 949
Titlu: "Heat"
Overview: "Obsessive master thief, Neil McCauley leads a top-notch crew 
on various insane heists throughout Los Angeles while a mentally unstable 
detective, Vincent Hanna pursues him without rest. Each man recognizes 
and respects the ability and the dedication of the other even though 
they are aware their cat-and-mouse game may end in violence."
Lungime: 400+ caractere

AVANTAJ: Filtrarea pe conținut poate extrage multe feature-uri.
```

---

### Exemplul 2: Film cu MULTE vs PUȚINE voturi (Popularitate)

**🔴 Film cu PUȚINE VOTURI (Long Tail):**
```
ID: 31357
Titlu: "Waiting to Exhale"
Vote Count: 34 voturi
Vote Average: 6.1

PROBLEMĂ: Filtrarea colaborativă nu are suficiente date.
SOLUȚIE: Folosim filtrarea pe conținut (genres: Comedy, Drama, Romance)
```

**🟢 Film cu MULTE VOTURI (Popular):**
```
ID: 862
Titlu: "Toy Story"
Vote Count: 5,415 voturi
Vote Average: 7.7

AVANTAJ: Filtrarea colaborativă funcționează excelent.
Mulți utilizatori au dat rating, deci putem găsi pattern-uri.
```

---

### Exemplul 3: Distribuția Rating-urilor

```
Analiza ratings_small.csv (100,004 rating-uri):

Rating    Număr       Procent
----------------------------------------
0.5       1,101       1.1%
1.0       3,326       3.3%
1.5       1,687       1.7%
2.0       7,271       7.3%
2.5       4,449       4.4%
3.0       20,064      20.1%    ← Cel mai comun
3.5       10,538      10.5%
4.0       28,750      28.7%    ← Al doilea cel mai comun
4.5       7,723       7.7%
5.0       15,095      15.1%

OBSERVAȚIE: Distribuție ușor skewed spre rating-uri pozitive.
Utilizatorii tind să acorde rating-uri > 3.
```

---

# 3. MODELUL UTILIZATORULUI (2 puncte)

## Date Colectate despre Utilizator

### A. Date Explicite (solicitate)
```
┌─────────────────────────────────────────────────┐
│          ÎNREGISTRARE UTILIZATOR NOU            │
│                                                 │
│  Selectează genurile preferate:                 │
│  ☑ Action    ☐ Comedy    ☑ Sci-Fi              │
│  ☐ Drama     ☑ Thriller  ☐ Horror              │
│                                                 │
│  Regizori preferați (opțional):                 │
│  [Christopher Nolan, Denis Villeneuve        ]  │
│                                                 │
│            [Salvează Preferințe]                │
└─────────────────────────────────────────────────┘
```

### B. Date Implicite (colectate automat)
```python
# Interacțiuni înregistrate automat:

1. Rating-uri (1-5 stele)
   → Utilizate pentru filtrare colaborativă
   
2. Vizualizări detalii film
   → Indică interes chiar fără rating
   
3. Timestamp interacțiuni
   → Permite să detectăm schimbări în preferințe
```

---

## Structura Profilului Utilizatorului

```python
user_profile = {
    # Identificare
    "user_id": "uuid-12345",
    
    # Preferințe explicite (Cold Start)
    "preferred_genres": ["Action", "Sci-Fi", "Thriller"],
    "preferred_directors": ["Christopher Nolan"],
    
    # Istoric de interacțiuni
    "ratings": [
        {"movie_id": "27205", "rating": 5.0, "timestamp": 1609459200},  # Inception
        {"movie_id": "157336", "rating": 4.5, "timestamp": 1609545600}, # Interstellar
        {"movie_id": "155", "rating": 5.0, "timestamp": 1609632000},    # Dark Knight
    ],
    
    # Profil derivat (calculat automat)
    "implicit_preferences": {
        "avg_rating": 4.83,
        "favorite_genres": ["Sci-Fi", "Action"],
        "preferred_runtime": "120-180 min",
        "activity_level": "active"
    }
}
```

---

## Cum sunt folosite datele?

```
┌────────────────────┐      ┌─────────────────────┐
│  Preferințe        │ ───► │  Filtrare pe        │
│  explicite         │      │  Conținut           │
│  (genuri, regizori)│      │  (pentru Cold Start)│
└────────────────────┘      └─────────────────────┘
                                     │
                                     ▼
┌────────────────────┐      ┌─────────────────────┐
│  Rating-uri        │ ───► │  Filtrare           │
│  implicite         │      │  Colaborativă       │
│  (1-5 stele)       │      │  (User & Item Based)│
└────────────────────┘      └─────────────────────┘
                                     │
                                     ▼
                            ┌─────────────────────┐
                            │  MODEL HIBRID       │
                            │  Recomandări        │
                            │  Personalizate      │
                            └─────────────────────┘
```

---

# 4. LONG TAIL / ALTE PROBLEME (2 puncte)

## Problema 1: COLD START

### User Cold Start (Utilizator Nou)

**Problemă:** Nu avem istoric de rating-uri pentru utilizatori noi.

**Soluție implementată:**

```python
def get_recommendations_for_new_user(self, preferred_genres, count=10):
    """
    Pentru utilizatori noi: DOAR filtrare pe conținut.
    """
    # Construim filtru bazat pe genuri selectate la înregistrare
    genre_filters = [f"'{g}' in 'genres'" for g in preferred_genres]
    filter_expression = ' or '.join(genre_filters)
    
    # Booster pentru filme populare (rezolvă și cold start)
    booster = "'vote_average' * (if 'vote_count' > 1000 then 1.5 else 1)"
    
    response = self.client.send(RecommendItemsToUser(
        'cold_start_temp',
        count,
        filter=filter_expression,
        booster=booster,
        logic={'name': 'recombee:content-based'}  # DOAR conținut
    ))
```

### Item Cold Start (Film Nou)

**Problemă:** Filmele noi nu au rating-uri de la utilizatori.

**Soluție:** Folosim metadatele filmului:

```python
def get_similar_movies(self, movie_id, count=10):
    """
    Pentru filme noi: similaritate bazată pe atribute.
    """
    # Recombee compară: genres, keywords, director, actors
    response = self.client.send(RecommendItemsToItem(
        str(movie_id),
        'similar_movies',
        count,
        logic={'name': 'recombee:hybrid'}
    ))
```

---

## Problema 2: LONG TAIL

**Definiție:** Majoritatea filmelor au foarte puține rating-uri, în timp ce un număr mic de filme populare domină.

### Distribuția în dataset:

```
                    LONG TAIL DISTRIBUTION
    │
    │█████████████                      
    │█████████████                        
    │█████████████                        
    │█████████████                        
    │█████████████ █                       Filme Populare
    │█████████████ ██                      (vote_count > 1000)
    │█████████████ ███                     ~5% din total
Voturi│█████████████ █████                    
    │█████████████ ████████               
    │█████████████ █████████████████████████████████████
    └────────────────────────────────────────────────────►
                       Filme (sortate după popularitate)
                       
                       ◄──── Long Tail ────►
                       ~95% din filme
```

### Soluție pentru Long Tail:

```python
# 1. Factor de diversitate în recomandări
diversity = 0.3  # 30% diversitate

# 2. Booster pentru filme cu rating bun dar mai puține voturi
booster = """
    'vote_average' * 
    (if 'vote_count' < 500 AND 'vote_average' > 7 then 1.3 else 1)
"""

# 3. Filtrare pe conținut pentru filme din long tail
# Când un film are puține rating-uri, ne bazăm pe atribute
```

---

## Problema 3: Sparsity (Raritate Date)

**Problemă:** Matricea User-Item este foarte rară (~99% valori lipsă).

```
              Film1  Film2  Film3  Film4  Film5  ...  Film45000
User1          5      ?      ?      3      ?          ?
User2          ?      4      ?      ?      ?          ?
User3          ?      ?      ?      ?      2          ?
...
User671        ?      ?      5      ?      ?          ?

? = Rating necunoscut (99%+ din matrice)
```

**Soluție:** 
- Recombee folosește factorizare matriceală (Matrix Factorization)
- Abordarea hibridă compensează cu filtrare pe conținut

---

# 5. DEMO (2 puncte)

## Pornire Aplicație

```bash
# 1. Instalare dependențe
pip install -r requirements.txt

# 2. Pornire server
python app.py

# 3. Accesează în browser
http://localhost:5000
```

---

## Screenshots Demo

### Pagina Principală - Recomandări
```
┌────────────────────────────────────────────────────────┐
│  🎬 CineMatch                      👤 Utilizator Nou   │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ✨ Ești nou aici?                                     │
│  Spune-ne ce genuri îți plac! [Setează Preferințe]     │
│                                                        │
│  🎭 Filtrează după gen:                                │
│  [Toate] [Acțiune] [Comedie] [Drama] [Sci-Fi] ...      │
│                                                        │
│  🎯 Recomandate pentru tine    [🔀 Abordare Hibridă]   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Poster  │ │ Poster  │ │ Poster  │ │ Poster  │       │
│  │         │ │         │ │         │ │         │       │
│  │  ★ 8.3  │ │  ★ 7.7  │ │  ★ 8.5  │ │  ★ 7.9  │       │
│  ├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤       │
│  │Inception│ │Toy Story│ │Godfather│ │ Matrix  │       │
│  │ Sci-Fi  │ │Animation│ │  Crime  │ │ Action  │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
│                                                        │
│  🔥 Filme Populare (Cold Start)                        │
│  [Interstellar] [Dark Knight] [Pulp Fiction] ...       │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Pagina Înregistrare (Cold Start)
```
┌────────────────────────────────────────────────────────┐
│  ✨ Bun venit la CineMatch!                            │
├────────────────────────────────────────────────────────┤
│                                                        │
│  🧊 Problema Cold Start                                │
│  Nu avem informații despre preferințele tale.          │
│  Selectează genurile preferate pentru primele          │
│  recomandări!                                          │
│                                                        │
│  🎭 Selectează genurile preferate:                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ 🎬      │ │ 😂      │ │ 😢      │ │ 👻      │       │
│  │ Action  │ │ Comedy  │ │ Drama   │ │ Horror  │       │
│  │   ☑     │ │   ☐     │ │   ☑     │ │   ☐     │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
│                                                        │
│  3 genuri selectate                                    │
│                                                        │
│           [🚀 Salvează și vezi recomandări]            │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Pagina Detalii Film + Rating
```
┌────────────────────────────────────────────────────────┐
│  🎬 CineMatch                                          │
├────────────────────────────────────────────────────────┤
│  ┌──────────┐                                          │
│  │          │  INCEPTION                               │
│  │  Poster  │  📅 2010  ⏱️ 148 min  ⭐ 8.3             │
│  │          │                                          │
│  │          │  [Sci-Fi] [Action] [Thriller]            │
│  └──────────┘                                          │
│                                                        │
│  Descriere:                                            │
│  A skilled thief who commits corporate espionage...    │
│                                                        │
│  ⭐ Dă un rating:                                      │
│  Rating-ul tău ajută sistemul să învețe preferințele!  │
│  [★] [★] [★] [★] [☆]  → 4/5                           │
│  ✅ Rating salvat! Mulțumim pentru feedback.           │
│                                                        │
│  🎬 Filme Similare (Item-Based Filtering):             │
│  [Interstellar] [The Dark Knight] [The Matrix]         │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## Flux Demo Live

1. **Start** → Pagina principală (utilizator nou)
2. **Click** "Setează Preferințe" → Cold Start
3. **Selectez** genuri: Sci-Fi, Action, Thriller
4. **Salvez** → Revin la homepage cu recomandări personalizate
5. **Click** pe un film → Pagina detalii
6. **Dau rating** 5 stele → Mesaj confirmare
7. **Văd** "Filme Similare" (Item-Based)
8. **Revin** la homepage → Recomandările s-au actualizat

---

# 📊 Rezumat Punctaj

| Cerință | Puncte | Status |
|---------|--------|--------|
| Funcționalitate SR | 2p | ✅ Sistem hibrid cu pseudocod |
| Dataset | 2p | ✅ Descriere + 3 exemple particulare |
| Model utilizator | 2p | ✅ Date explicite + implicite |
| Long tail/probleme | 2p | ✅ Cold Start + Long Tail + Sparsity |
| Demo | 2p | ✅ Aplicație web funcțională |
| **TOTAL** | **10p** | ✅ |

---

# Referințe

- Dataset: https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset
- Recombee API: https://www.recombee.com/
- Flask: https://flask.palletsprojects.com/

