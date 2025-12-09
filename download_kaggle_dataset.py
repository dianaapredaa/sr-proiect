#!/usr/bin/env python3
"""
Script pentru descărcarea automată a dataset-ului de pe Kaggle

Acest script:
1. Verifică configurația Kaggle API
2. Descarcă "The Movies Dataset" de pe Kaggle
3. Extrage fișierele în directorul dataset/
4. Verifică integritatea datelor

Utilizare:
    python download_kaggle_dataset.py
"""

import os
import sys
import zipfile
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi
import config


def check_kaggle_credentials():
    """Verifică dacă credențialele Kaggle sunt configurate."""
    print("🔍 Verificare credențiale Kaggle...")
    
    # Verifică fișierul kaggle.json
    kaggle_dir = Path.home() / '.kaggle'
    kaggle_json = kaggle_dir / 'kaggle.json'
    
    if kaggle_json.exists():
        print(f"✅ Găsit kaggle.json în {kaggle_json}")
        # Verifică permisiunile
        stat = os.stat(kaggle_json)
        mode = oct(stat.st_mode)[-3:]
        if mode != '600':
            print(f"⚠️  Permisiuni incorecte pentru kaggle.json: {mode}")
            print(f"   Rulează: chmod 600 {kaggle_json}")
            return False
        return True
    
    # Verifică variabile de mediu
    if os.getenv('KAGGLE_USERNAME') and os.getenv('KAGGLE_KEY'):
        print("✅ Găsite credențiale în variabile de mediu")
        return True
    
    print("❌ Credențiale Kaggle nu sunt configurate!")
    print("\n📝 Pași pentru configurare:")
    print("   1. Mergi pe https://www.kaggle.com/settings")
    print("   2. Click pe 'Create New Token' în secțiunea API")
    print("   3. Descarcă kaggle.json")
    print("   4. Copiază în ~/.kaggle/kaggle.json")
    print("   5. Rulează: chmod 600 ~/.kaggle/kaggle.json")
    print("\n   SAU setează variabile de mediu:")
    print("   export KAGGLE_USERNAME='your-username'")
    print("   export KAGGLE_KEY='your-api-key'")
    
    return False


def authenticate_kaggle():
    """Autentifică cu Kaggle API."""
    try:
        api = KaggleApi()
        api.authenticate()
        print("✅ Autentificare Kaggle reușită")
        return api
    except Exception as e:
        print(f"❌ Eroare la autentificare Kaggle: {e}")
        return None


def check_dataset_terms():
    """Verifică dacă termenii dataset-ului au fost acceptați."""
    print("\n📋 Verificare termeni dataset...")
    print("⚠️  IMPORTANT: Trebuie să accepți termenii dataset-ului pe Kaggle!")
    print("   Mergi pe: https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset")
    print("   Click pe 'New Notebook' sau 'Download' pentru a accepta termenii")
    
    response = input("\nAi acceptat deja termenii? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Acceptă termenii pe site-ul Kaggle și încearcă din nou")
        return False
    
    return True


def create_dataset_dir():
    """Creează directorul pentru dataset dacă nu există."""
    dataset_dir = Path(config.DATA_DIR)
    dataset_dir.mkdir(exist_ok=True)
    print(f"📁 Director dataset: {dataset_dir.absolute()}")
    return dataset_dir


def download_dataset(api, dataset_dir):
    """Descarcă dataset-ul de pe Kaggle."""
    dataset_name = 'rounakbanik/the-movies-dataset'
    
    print(f"\n📥 Descărcare dataset: {dataset_name}")
    print("   Aceasta poate dura câteva minute...")
    
    try:
        # Descarcă dataset-ul
        api.dataset_download_files(
            dataset_name,
            path=str(dataset_dir),
            unzip=True,
            quiet=False
        )
        print("✅ Dataset descărcat cu succes!")
        return True
    except Exception as e:
        print(f"❌ Eroare la descărcare: {e}")
        
        if "403" in str(e) or "Forbidden" in str(e):
            print("\n💡 Posibile soluții:")
            print("   1. Verifică că ai acceptat termenii dataset-ului")
            print("   2. Verifică că token-ul tău Kaggle este valid")
            print("   3. Mergi pe site-ul Kaggle și acceptă termenii manual")
        
        return False


def verify_downloaded_files(dataset_dir):
    """Verifică dacă fișierele necesare au fost descărcate."""
    print("\n🔍 Verificare fișiere descărcate...")
    
    required_files = [
        'movies_metadata.csv',
        'keywords.csv',
        'credits.csv',
        'ratings.csv',
        'ratings_small.csv'
    ]
    
    missing = []
    found = []
    
    for filename in required_files:
        filepath = dataset_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"   ✅ {filename} ({size_mb:.1f} MB)")
            found.append(filename)
        else:
            print(f"   ❌ {filename} - LIPSĂ")
            missing.append(filename)
    
    # Verifică și fișierele din zip dacă există
    zip_files = list(dataset_dir.glob('*.zip'))
    if zip_files:
        print(f"\n📦 Găsite {len(zip_files)} fișiere zip")
        for zip_file in zip_files:
            print(f"   - {zip_file.name}")
            print("   💡 Extragere manuală necesară sau deja extras")
    
    if missing:
        print(f"\n⚠️  {len(missing)} fișiere lipsesc: {', '.join(missing)}")
        return False
    
    print(f"\n✅ Toate fișierele necesare sunt prezente ({len(found)}/{len(required_files)})")
    return True


def extract_zip_if_needed(dataset_dir):
    """Extrage fișierele zip dacă există."""
    zip_files = list(dataset_dir.glob('*.zip'))
    
    if not zip_files:
        return True
    
    print(f"\n📦 Extragere {len(zip_files)} fișiere zip...")
    
    for zip_file in zip_files:
        try:
            print(f"   Extragere {zip_file.name}...")
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(dataset_dir)
            print(f"   ✅ {zip_file.name} extras")
            
            # Opțional: șterge zip-ul după extragere
            # zip_file.unlink()
        except Exception as e:
            print(f"   ❌ Eroare la extragere {zip_file.name}: {e}")
            return False
    
    return True


def main():
    """Funcția principală."""
    print("=" * 60)
    print("🎬 DESCĂRCARE DATASET KAGGLE - THE MOVIES DATASET")
    print("=" * 60)
    
    # Verifică credențiale
    if not check_kaggle_credentials():
        sys.exit(1)
    
    # Autentifică
    api = authenticate_kaggle()
    if not api:
        sys.exit(1)
    
    # Verifică termeni
    if not check_dataset_terms():
        sys.exit(1)
    
    # Creează directorul
    dataset_dir = create_dataset_dir()
    
    # Descarcă dataset-ul
    if not download_dataset(api, dataset_dir):
        sys.exit(1)
    
    # Extrage zip-uri dacă există
    extract_zip_if_needed(dataset_dir)
    
    # Verifică fișierele
    if not verify_downloaded_files(dataset_dir):
        print("\n⚠️  Unele fișiere lipsesc, dar descărcarea a continuat")
        print("   Verifică manual directorul dataset/")
    
    print("\n" + "=" * 60)
    print("✅ DESCĂRCARE COMPLETĂ!")
    print("=" * 60)
    print(f"\n📁 Fișierele sunt în: {dataset_dir.absolute()}")
    print("\n🚀 Următorul pas: Configurează Recombee și rulează:")
    print("   python load_data.py --test")
    print("\n📖 Vezi SETUP_KAGGLE_RECOMBEE.md pentru detalii complete")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Descărcare întreruptă de utilizator")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Eroare neașteptată: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

