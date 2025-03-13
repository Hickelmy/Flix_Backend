import os
import requests
import zipfile
import shutil
import pandas as pd
import mysql.connector
import re
from sqlalchemy import create_engine, Column, Integer, String, DECIMAL, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, sessionmaker, DeclarativeBase
from datetime import datetime

# 🔹 Configuração do MySQL
DB_USER = "root"
DB_PASSWORD = "admin"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "movielens"

# 🔹 Criar banco de dados se não existir
print("🔍 Verificando banco de dados MySQL...")
conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
cursor = conn.cursor()
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
conn.commit()
conn.close()
print(f"✅ Banco de dados `{DB_NAME}` pronto.")

# 🔹 Conectar ao MySQL com SQLAlchemy
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 📌 Diretórios organizados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MOVIELENS_DIR = os.path.join(DATA_DIR, "movielens")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
IMAGES_CSV = os.path.join(IMAGES_DIR, "ml1m-images-master", "ml1m_images.csv")

DATASET_URL = "https://files.grouplens.org/datasets/movielens/ml-1m.zip"
IMAGES_ZIP_URL = "https://github.com/antonsteenvoorden/ml1m-images/archive/refs/heads/master.zip"

# Criar pastas organizadas se não existirem
os.makedirs(MOVIELENS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


class Base(DeclarativeBase):
    pass


# 📌 Modelos do banco
class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    year = Column(Integer, nullable=True)
    genres = Column(String(255), nullable=False)
    image_base64 = Column(Text, nullable=True)  # 🔹 Agora armazena apenas o link da imagem
    ratings = relationship("Rating", back_populates="movie", cascade="all, delete")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    gender = Column(String(10), nullable=False)
    age = Column(Integer, nullable=False)
    occupation = Column(Integer, nullable=False)
    zip_code = Column(String(20), nullable=False)
    ratings = relationship("Rating", back_populates="user", cascade="all, delete")


class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    rating = Column(DECIMAL(3, 2), nullable=False)
    timestamp = Column(DateTime, nullable=False)

    movie = relationship("Movie", back_populates="ratings")
    user = relationship("User", back_populates="ratings")


# 📌 Criar tabelas no banco MySQL
Base.metadata.create_all(bind=engine)
print("✅ Estrutura do banco de dados criada.")


# 📌 Baixar e extrair arquivos ZIP corretamente
def download_and_extract_zip(url, extract_to):
    zip_file_path = os.path.join(DATA_DIR, os.path.basename(url))

    if not os.path.exists(zip_file_path):
        print(f"📥 Baixando {url}...")
        response = requests.get(url, verify=False, stream=True)
        with open(zip_file_path, "wb") as file:
            file.write(response.content)

    print(f"📦 Extraindo arquivos para {extract_to}...")
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

    print(f"✅ Arquivos extraídos em {extract_to}")


# 📌 Verificar se os arquivos já existem
def files_exist():
    return all(os.path.exists(os.path.join(MOVIELENS_DIR, file)) for file in ["movies.dat", "users.dat", "ratings.dat"])


def images_csv_exists():
    return os.path.exists(IMAGES_CSV)


# 📌 Função para carregar arquivos `.dat`
def load_dat_file(filename, delimiter="::", columns=None):
    file_path = os.path.join(MOVIELENS_DIR, filename)

    if not os.path.exists(file_path):
        print(f"❌ ERRO: Arquivo não encontrado: {file_path}")
        return None

    return pd.read_csv(file_path, delimiter=delimiter, header=None, names=columns, engine="python", encoding="ISO-8859-1")


# 📌 Função para carregar `ml1m_images.csv` e mapear os links das imagens
def fetch_image_links():
    if not images_csv_exists():
        print("❌ ERRO: Arquivo ml1m_images.csv não encontrado!")
        return {}

    images_df = pd.read_csv(IMAGES_CSV)
    images_dict = dict(zip(images_df["item_id"], images_df["image"]))

    print(f"✅ {len(images_dict)} imagens vinculadas a filmes via URL.")
    return images_dict


# 📌 Extração de dados do MovieLens
def extract_year_from_title(title):
    """Extrai o ano do título do filme e retorna o título limpo e o ano."""
    match = re.search(r"\((\d{4})\)", title)
    year = int(match.group(1)) if match else None
    clean_title = re.sub(r"\(\d{4}\)", "", title).strip()
    return clean_title, year


def extract_data():
    if not files_exist():
        print("📥 Baixando e extraindo arquivos do MovieLens...")
        download_and_extract_zip(DATASET_URL, MOVIELENS_DIR)

    if not images_csv_exists():
        print("📥 Baixando imagens...")
        download_and_extract_zip(IMAGES_ZIP_URL, IMAGES_DIR)

    print("🔄 Extraindo dados do MovieLens...")
    movies = load_dat_file("movies.dat", columns=["id", "title", "genres"])
    users = load_dat_file("users.dat", columns=["id", "gender", "age", "occupation", "zip_code"])
    ratings = load_dat_file("ratings.dat", columns=["user_id", "movie_id", "rating", "timestamp"])

    if any(df is None or df.empty for df in [movies, users, ratings]):
        print("❌ ERRO: Arquivos não carregados corretamente ou vazios.")
        return None

    ratings["timestamp"] = pd.to_datetime(ratings["timestamp"], unit="s")

    # Extrair ano do título
    movies["title"], movies["year"] = zip(*movies["title"].map(extract_year_from_title))

    return {"movies": movies, "users": users, "ratings": ratings}


# 📌 Carregar dados no banco MySQL
def load_data_to_db(data):
    session = SessionLocal()
    images_dict = fetch_image_links()

    for _, row in data["movies"].iterrows():
        movie = session.query(Movie).filter_by(id=row["id"]).first()
        if not movie:
            session.add(Movie(
                id=row["id"],
                title=row["title"],
                year=row["year"],
                genres=row["genres"],
                image_base64=images_dict.get(row["id"], None)
            ))
    session.commit()
    session.close()
    print("✅ Dados carregados no banco com sucesso!")


# 📌 Executar o ETL
def run_etl():
    data = extract_data()
    if data:
        load_data_to_db(data)
        print("✅ ETL finalizado com sucesso!")


if __name__ == "__main__":
    run_etl()
