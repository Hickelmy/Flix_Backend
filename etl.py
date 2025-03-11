import os
import pandas as pd
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Movie, Rating, Tag

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "ml-32m")

def load_csv(filename, chunksize=10000):
    file_path = os.path.join(DATASET_PATH, filename)

    if not os.path.exists(file_path):
        print(f"❌ ERRO: Arquivo não encontrado: {file_path}")
        return None

    try:
        return pd.read_csv(file_path, chunksize=chunksize) 
    except Exception as e:
        print(f"❌ ERRO ao ler {filename}: {e}")
        return None

def extract_data():
    print(f"🔄 Extraindo dados de: {DATASET_PATH}")

    csv_files = ["movies.csv", "ratings.csv", "tags.csv"]
    data = {file.split(".")[0]: load_csv(file) for file in csv_files}

    if any(df is None for df in data.values()):
        print("❌ ERRO: Um ou mais arquivos CSV não foram carregados corretamente.")
        return None

    return data

def transform_data(movies_df):
    movies_df["year"] = movies_df["title"].str.extract(r"\((\d{4})\)").fillna(0).astype(int)
    movies_df["title"] = movies_df["title"].str.replace(r"\(\d{4}\)", "", regex=True).str.strip()
    movies_df["genres"] = movies_df["genres"].fillna("")
    return movies_df

def load_data_to_db(data):
    print("📦 Carregando dados no banco...")

    if data is None:
        print("❌ ERRO: Dados inválidos, abortando o carregamento.")
        return

    session = SessionLocal()

    for movies_chunk in data["movies"]:
        movies_df = transform_data(movies_chunk)
        movies_bulk = movies_df.to_dict(orient="records")
        session.bulk_insert_mappings(Movie, movies_bulk)
        session.commit()
        print(f"✅ {len(movies_bulk)} filmes carregados.")

    for ratings_chunk in data["ratings"]:
        ratings_bulk = ratings_chunk.to_dict(orient="records")
        session.bulk_insert_mappings(Rating, ratings_bulk)
        session.commit()
        print(f"✅ {len(ratings_bulk)} avaliações carregadas.")

    for tags_chunk in data["tags"]:
        tags_bulk = tags_chunk.to_dict(orient="records")
        session.bulk_insert_mappings(Tag, tags_bulk)
        session.commit()
        print(f"✅ {len(tags_bulk)} tags carregadas.")

    session.close()
    print("✅ Todos os dados foram carregados com sucesso!")

def run_etl():
    data = extract_data()
    if data:
        load_data_to_db(data)

if __name__ == "__main__":
    run_etl()
