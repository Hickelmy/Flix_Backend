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
from passlib.context import CryptContext

# 🔹 Configuração do MySQL
DB_CONFIG = {
    "user": "root",
    "password": "senha123",
    "host": "localhost",
    "port": "3306",
    "database": "movielens"
}

# 🔹 Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MOVIELENS_DIR = os.path.join(DATA_DIR, "movielens")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
IMAGES_CSV_PATH = os.path.join(IMAGES_DIR, "ml1m-images-master", "ml1m_images.csv")

# URLs dos datasets
DATASET_URL = "https://files.grouplens.org/datasets/movielens/ml-1m.zip"
IMAGES_ZIP_URL = "https://github.com/antonsteenvoorden/ml1m-images/archive/refs/heads/master.zip"

# Criar pastas se não existirem
os.makedirs(MOVIELENS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# 🔹 Criar banco de dados se não existir
def create_database():
    conn = mysql.connector.connect(
        host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"]
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.commit()
    conn.close()
    print(f"✅ Banco de dados `{DB_CONFIG['database']}` pronto.")

create_database()

# 🔹 Conectar ao MySQL
DATABASE_URL = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


# 📌 Modelos do banco (Agora com `login`)
class Login(Base):
    __tablename__ = "login"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)


# 📌 Modelos do banco
class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    year = Column(Integer, nullable=True)
    genres = Column(String(255), nullable=False)
    image_base64 = Column(Text, nullable=True)
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

# Criar tabelas
Base.metadata.create_all(bind=engine)

def create_admin_user():
    session = SessionLocal()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Verifica se o usuário já existe
    admin_user = session.query(Login).filter(Login.username == "admin").first()
    if not admin_user:
        hashed_password = pwd_context.hash("admin")  # Senha criptografada
        new_admin = Login(username="admin", password_hash=hashed_password)
        session.add(new_admin)
        session.commit()
        print("✅ Usuário `admin` criado com sucesso!")
    else:
        print("🔹 Usuário `admin` já existe.")

    session.close()

create_admin_user()


# 📌 Baixar arquivos ZIP
def download_file(url, save_path):
    if not os.path.exists(save_path):
        print(f"📥 Baixando {url}...")
        response = requests.get(url, verify=False, stream=True)
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"✅ Download concluído: {save_path}")

# 📌 Extrair arquivos ZIP e mover arquivos corretamente
def extract_zip(zip_path, extract_to):
    if not os.path.exists(extract_to) or not os.listdir(extract_to):
        print(f"📦 Extraindo arquivos para {extract_to}...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)

        # Mover arquivos do diretório `ml-1m/` para `movielens/`
        extracted_subdir = os.path.join(extract_to, "ml-1m")
        if os.path.exists(extracted_subdir):
            for file in os.listdir(extracted_subdir):
                shutil.move(os.path.join(extracted_subdir, file), os.path.join(extract_to, file))
            shutil.rmtree(extracted_subdir)

        print(f"✅ Extração concluída!")
    else:
        print(f"📁 Arquivos já extraídos em: {extract_to}")

# 📌 Processar e carregar dados
def extract_data():
    movies_path = os.path.join(MOVIELENS_DIR, "movies.dat")
    users_path = os.path.join(MOVIELENS_DIR, "users.dat")
    ratings_path = os.path.join(MOVIELENS_DIR, "ratings.dat")

    if not os.path.exists(movies_path):
        raise FileNotFoundError(f"❌ ERRO: Arquivo `{movies_path}` não encontrado!")

    movies = pd.read_csv(movies_path, delimiter="::",
                         names=["id", "title", "genres"], engine="python", encoding="ISO-8859-1")

    movies["id"] = movies["id"].astype(int)
    movies["year"] = movies["title"].str.extract(r"\((\d{4})\)").fillna(0).astype(int)
    movies["title"] = movies["title"].str.replace(r"\(\d{4}\)", "", regex=True).str.strip()

    users = pd.read_csv(users_path, delimiter="::",
                        names=["id", "gender", "age", "occupation", "zip_code"], engine="python",
                        encoding="ISO-8859-1").astype({"id": int, "age": int, "occupation": int})

    ratings = pd.read_csv(ratings_path, delimiter="::",
                          names=["user_id", "movie_id", "rating", "timestamp"], engine="python",
                          encoding="ISO-8859-1").astype({"user_id": int, "movie_id": int, "rating": float})

    ratings["timestamp"] = ratings["timestamp"].astype(int).apply(lambda x: datetime.utcfromtimestamp(x))

    return {"movies": movies, "users": users, "ratings": ratings}

# 📌 Inserir dados no banco
def load_data_to_db(data):
    session = SessionLocal()
    print("📥 Inserindo dados no banco...")
    session.bulk_insert_mappings(Movie, data["movies"].to_dict(orient="records"))
    session.bulk_insert_mappings(User, data["users"].to_dict(orient="records"))
    session.bulk_insert_mappings(Rating, data["ratings"].to_dict(orient="records"))
    session.commit()
    session.close()
    print("✅ Dados carregados com sucesso!")

# 📌 Atualizar imagens dos filmes
def insert_image_to_db():
    session = SessionLocal()
    if not os.path.exists(IMAGES_CSV_PATH):
        print("❌ ERRO: Arquivo ml1m_images.csv não encontrado!")
        return

    images_df = pd.read_csv(IMAGES_CSV_PATH, encoding="ISO-8859-1")
    image_dict = dict(zip(images_df["item_id"], images_df["image"]))

    existing_movies = session.query(Movie).filter(Movie.id.in_(image_dict.keys())).all()

    for movie in existing_movies:
        movie.image_base64 = image_dict.get(movie.id)

    session.commit()
    session.close()
    print(f"✅ {len(existing_movies)} filmes atualizados com imagens.")

# 📌 Executar ETL
def run_etl():
    print("🚀 Iniciando processo ETL...")

    download_file(DATASET_URL, os.path.join(DATA_DIR, "ml-1m.zip"))
    download_file(IMAGES_ZIP_URL, os.path.join(DATA_DIR, "ml1m-images.zip"))

    extract_zip(os.path.join(DATA_DIR, "ml-1m.zip"), MOVIELENS_DIR)
    extract_zip(os.path.join(DATA_DIR, "ml1m-images.zip"), IMAGES_DIR)

    data = extract_data()
    load_data_to_db(data)
    insert_image_to_db()

    create_admin_user()

    print("✅ ETL finalizado com sucesso!")

if __name__ == "__main__":
    run_etl()
