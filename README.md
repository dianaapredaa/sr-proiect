# 🎬 CineMatch - Sistem de Recomandare Filme

**Proiect Sisteme de Recomandare**  
*Diana Preda & Omer Tarik - E-Guvernare*

---

## 📋 Descriere

CineMatch este un sistem inteligent de recomandare filme care utilizează o **abordare hibridă**, combinând:

1. **Filtrare Colaborativă** - Analizează similaritățile între utilizatori și filme bazate pe rating-uri
2. **Filtrare Bazată pe Conținut** - Analizează metadatele filmelor (gen, regizor, actori, keywords)

Sistemul rezolvă problema **Cold Start** (pornire la rece) pentru utilizatori și filme noi prin:
- Solicitarea preferințelor inițiale de la utilizatorii noi
- Utilizarea metadatelor pentru filmele fără rating-uri

---

## 🛠️ Tehnologii Utilizate

- **Backend**: Python 3.9+, Flask
- **API Recomandări**: [Recombee](https://www.recombee.com/) - platformă de recomandare ca serviciu
- **Dataset**: [The Movies Dataset](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset) de pe Kaggle
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)

---

## 📁 Structura Proiectului

```
proiect/
├── app.py                 # Aplicația Flask principală
├── config.py              # Configurări
├── data_loader.py         # Încărcare și procesare date Kaggle
├── recombee_client.py     # Client pentru API-ul Recombee
├── load_data.py           # Script pentru încărcarea datelor în Recombee
├── requirements.txt       # Dependențe Python
├── env.example            # Template pentru variabilele de mediu
├── README.md              # Documentație
├── dataset/               # Directorul pentru datele Kaggle (deja inclus!)
│   ├── movies_metadata.csv
│   ├── keywords.csv
│   ├── credits.csv
│   ├── ratings.csv
│   └── ratings_small.csv
├── static/
│   ├── css/
│   │   └── style.css      # Stiluri CSS
│   └── js/
│       └── main.js        # JavaScript principal
└── templates/
    ├── base.html          # Template de bază
    ├── index.html         # Pagina principală
    ├── register.html      # Înregistrare preferințe (Cold Start)
    └── movie.html         # Detalii film
```

---

## 🚀 Instalare și Configurare

### 1. Clonează sau descarcă proiectul

```bash
cd proiect
```

### 2. Creează un mediu virtual Python

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# sau
venv\Scripts\activate     # Windows
```

### 3. Instalează dependențele

```bash
pip install -r requirements.txt
```

### 4. Dataset-ul

✅ **Dataset-ul este deja inclus în proiect!**

Fișierele sunt în directorul `dataset/`:
- `movies_metadata.csv`
- `keywords.csv` 
- `credits.csv`
- `ratings.csv`

*Dacă vrei să folosești alt dataset, poți descărca de la [Kaggle](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset)*

### 5. Configurează Recombee (Opțional pentru funcționalitate completă)

1. Creează un cont gratuit pe [Recombee](https://www.recombee.com/)
2. Creează o bază de date nouă
3. Copiază `env.example` în `.env`
4. Completează credențialele:

```bash
cp env.example .env
# Editează .env cu credențialele tale
```

### 6. Încarcă datele în Recombee (dacă ai configurat)

```bash
# Mod test (100 filme, 1000 rating-uri)
python load_data.py --test

# Încărcare completă
python load_data.py
```

### 7. Pornește aplicația

```bash
python app.py
```

Accesează aplicația la: **http://localhost:5000**

---

## 🎯 Funcționalități

### Pagina Principală
- Afișează recomandări personalizate
- Filtrare după gen
- Secțiune cu filme populare
- Explicarea mecanismului de recomandare

### Pagina de Preferințe (Cold Start)
- Permite utilizatorilor noi să selecteze genurile preferate
- Rezolvă problema "User Cold Start"

### Pagina de Detalii Film
- Informații complete despre film
- Filme similare (Item-Based Collaborative Filtering)
- Posibilitatea de a da rating (alimentează filtrarea colaborativă)

---

## 🔧 Mecanismul de Recomandare

### 1. Filtrare Colaborativă

```
Utilizator A apreciază: Film1 ★★★★★, Film2 ★★★★☆, Film3 ★★★★★
Utilizator B apreciază: Film1 ★★★★★, Film2 ★★★★☆, Film4 ???

→ Sistemul recomandă Film3 lui B (bazat pe similaritatea cu A)
```

### 2. Filtrare Bazată pe Conținut

```
Filmul apreciat: "Inception" (Sci-Fi, Christopher Nolan, Thriller)
→ Sistemul recomandă: "Interstellar", "The Dark Knight", "Tenet"
```

### 3. Abordare Hibridă

Combină ambele metode pentru:
- Recomandări mai diverse
- Rezolvarea problemei Cold Start
- Îmbunătățirea preciziei

---

## 🧊 Problema Cold Start

### User Cold Start (Utilizator Nou)
- **Problemă**: Nu avem istoric pentru utilizatori noi
- **Soluție**: 
  1. Cerem preferințe la înregistrare
  2. Folosim filtrarea bazată pe conținut inițial
  3. Tranziționăm la hibrid pe măsură ce acumulăm date

### Item Cold Start (Film Nou)
- **Problemă**: Filmele noi nu au rating-uri
- **Soluție**: 
  1. Folosim metadatele filmului (gen, regizor, actori)
  2. Potrivim cu profilurile utilizatorilor existenți

---

## 🌐 API Endpoints

| Endpoint | Metodă | Descriere |
|----------|--------|-----------|
| `/api/recommendations` | GET | Obține recomandări personalizate |
| `/api/similar/<movie_id>` | GET | Filme similare |
| `/api/rate` | POST | Înregistrează un rating |
| `/api/user/register` | POST | Înregistrează preferințe utilizator |
| `/api/popular` | GET | Filme populare |
| `/api/movie/<movie_id>` | GET | Detalii film |
| `/api/genres` | GET | Lista de genuri |

---

## 📊 Dataset

**The Movies Dataset** include:
- **45.000+ filme** cu metadate complete
- **26 milioane rating-uri** de la 270.000 utilizatori
- Keywords și informații despre distribuție

### Fișiere utilizate:

| Fișier | Descriere |
|--------|-----------|
| `movies_metadata.csv` | Informații filme (titlu, gen, dată, rating mediu) |
| `keywords.csv` | Cuvinte cheie pentru fiecare film |
| `credits.csv` | Actori și echipă (pentru regizori) |
| `ratings.csv` | Rating-uri utilizatori |

---

## 🔑 Recombee API

Recombee este o platformă de recomandare ca serviciu care:
- Gestionează automat scalarea și antrenarea modelelor
- Oferă algoritmi hibrizi avansați
- Rezolvă eficient problema Cold Start
- Permite configurare flexibilă prin ReQL (query language)

---

## 🎨 Interfața Utilizator

Interfața are un design modern inspirat de platformele de streaming:
- Temă dark cinema
- Carduri interactive pentru filme
- Animații fluide
- Responsive design pentru mobile

---

## 📝 Exemple de Utilizare

### Obține recomandări pentru un utilizator:

```python
from recombee_client import MovieRecommender

recommender = MovieRecommender()
recommendations = recommender.get_recommendations_for_user(
    user_id='user123',
    count=10,
    filter_genres=['Action', 'Sci-Fi']
)
```

### Pentru utilizatori noi (Cold Start):

```python
recommendations = recommender.get_recommendations_for_new_user(
    preferred_genres=['Drama', 'Thriller'],
    count=10
)
```

---

## 🤝 Autori

- **Diana Preda** - E-Guvernare
- **Omer Tarik** - E-Guvernare

---

## 📚 Resurse

- [Recombee Documentation](https://docs.recombee.com/)
- [The Movies Dataset - Kaggle](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## 📄 Licență

Proiect educațional pentru cursul de Sisteme de Recomandare.

