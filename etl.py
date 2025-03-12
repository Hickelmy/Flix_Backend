import os
import requests
import zipfile
import shutil
import base64
import pandas as pd
from io import BytesIO
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, sessionmaker, DeclarativeBase
from datetime import datetime

# 📌 Configurações de diretórios e URLs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_URL = "https://files.grouplens.org/datasets/movielens/ml-1m.zip"
DATASET_PATH = os.path.join(BASE_DIR, "ml-1m")

IMAGES_ZIP_URL = "https://github.com/antonsteenvoorden/ml1m-images/archive/refs/heads/master.zip"
IMAGES_PATH = os.path.join(DATASET_PATH, "images")

DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'movielens_1m.db')}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 📌 Definição da base ORM
class Base(DeclarativeBase):
    pass

# 📌 Modelos do banco
class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    year = Column(Integer, nullable=True)
    genres = Column(String, nullable=False)
    image_base64 = Column(Text, nullable=True)
    ratings = relationship("Rating", back_populates="movie", cascade="all, delete")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    gender = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    occupation = Column(Integer, nullable=False)
    zip_code = Column(String, nullable=False)
    ratings = relationship("Rating", back_populates="user", cascade="all, delete")

class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    movie = relationship("Movie", back_populates="ratings")
    user = relationship("User", back_populates="ratings")

Base.metadata.create_all(bind=engine)

# 📌 Função para verificar se os arquivos já estão disponíveis
def files_exist():
    return all(os.path.exists(os.path.join(DATASET_PATH, file)) for file in ["movies.dat", "users.dat", "ratings.dat"])

def images_exist():
    return os.path.exists(IMAGES_PATH) and len(os.listdir(IMAGES_PATH)) > 1000  # Verifica se há imagens suficientes

# 📌 Função para baixar e extrair um ZIP
def download_and_extract_zip(url, extract_to):
    zip_file_path = os.path.join(BASE_DIR, os.path.basename(url))  

    if not os.path.exists(zip_file_path):
        print(f"📥 Baixando {url}...")
        response = requests.get(url, verify=False, stream=True)
        with open(zip_file_path, "wb") as file:
            file.write(response.content)

    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

    extracted_folder = os.path.join(extract_to, "ml-1m")
    if os.path.exists(extracted_folder):
        for file in os.listdir(extracted_folder):
            shutil.move(os.path.join(extracted_folder, file), extract_to)
        shutil.rmtree(extracted_folder)

    print(f"✅ Arquivos extraídos em {extract_to}")

# 📌 Função para converter imagens em Base64 e associá-las corretamente
def convert_images_to_base64():
    base64_images = {}

    if not os.path.exists(IMAGES_PATH):
        print(f"❌ ERRO: Pasta de imagens não encontrada em {IMAGES_PATH}")
        return base64_images

    for filename in os.listdir(IMAGES_PATH):
        if filename.endswith(".jpg"):
            movie_id = os.path.splitext(filename)[0]  
            image_path = os.path.join(IMAGES_PATH, filename)
            with open(image_path, "rb") as img_file:
                base64_images[int(movie_id)] = base64.b64encode(img_file.read()).decode("utf-8")  

    print(f"✅ {len(base64_images)} imagens convertidas para Base64.")
    return base64_images

# 📌 Função para carregar os arquivos `.dat`
def load_dat_file(filename, delimiter="::", columns=None):
    file_path = os.path.join(DATASET_PATH, filename)

    if not os.path.exists(file_path):
        print(f"❌ ERRO: Arquivo não encontrado: {file_path}")
        return None

    try:
        return pd.read_csv(file_path, delimiter=delimiter, header=None, names=columns, engine="python", encoding="ISO-8859-1")
    except Exception as e:
        print(f"❌ ERRO ao ler {filename}: {e}")
        return None

# 📌 Função para extrair os dados do MovieLens
def extract_data():
    if not files_exist():
        print("📥 Baixando e extraindo arquivos do MovieLens...")
        download_and_extract_zip(DATASET_URL, DATASET_PATH)

    if not images_exist():
        print("📥 Baixando imagens...")
        download_and_extract_zip(IMAGES_ZIP_URL, IMAGES_PATH)

    print("🔄 Extraindo dados do MovieLens...")

    movies = load_dat_file("movies.dat", columns=["id", "title", "genres"])
    users = load_dat_file("users.dat", columns=["id", "gender", "age", "occupation", "zip_code"])
    ratings = load_dat_file("ratings.dat", columns=["user_id", "movie_id", "rating", "timestamp"])

    if any(df is None for df in [movies, users, ratings]):
        print("❌ ERRO: Um ou mais arquivos .dat não foram carregados corretamente.")
        return None

    return {"movies": movies, "users": users, "ratings": ratings}

# 📌 Transformações
def transform_movies(movies_df, base64_images):
    # 🔹 Extração do ano e limpeza do título
    movies_df["year"] = movies_df["title"].str.extract(r"\((\d{4})\)").fillna(0).astype(int)
    movies_df["title"] = movies_df["title"].str.replace(r"\(\d{4}\)", "", regex=True).str.strip()
    
    # 🔹 Associação das imagens base64
    movies_df["image_base64"] = movies_df["id"].map(base64_images).fillna("")  
    return movies_df

def transform_ratings(ratings_df):
    ratings_df["timestamp"] = ratings_df["timestamp"].apply(lambda x: datetime.utcfromtimestamp(int(x)))
    return ratings_df

# 📌 Função para carregar os dados no banco de dados
def load_data_to_db(data):
    base64_images = convert_images_to_base64()

    with SessionLocal() as session:
        movies_df = transform_movies(data["movies"], base64_images)
        session.bulk_insert_mappings(Movie, movies_df.to_dict(orient="records"))
        session.commit()

        session.bulk_insert_mappings(User, data["users"].to_dict(orient="records"))
        session.commit()

        ratings_df = transform_ratings(data["ratings"])
        session.bulk_insert_mappings(Rating, ratings_df.to_dict(orient="records"))
        session.commit()

# 📌 Função principal do ETL
def run_etl():
    data = extract_data()
    if data:
        load_data_to_db(data)

# 📌 Executar o ETL
if __name__ == "__main__":
    run_etl()
