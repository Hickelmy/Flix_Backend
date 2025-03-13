import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.exc import OperationalError

# Configuração do MySQL
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "senha123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "movielens")

# String de conexão para MySQL
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Criando o motor de conexão com MySQL
engine = create_engine(DATABASE_URL, echo=False)

# Criando a sessão do banco de dados
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Base para modelos SQLAlchemy
Base = declarative_base()

def init_db():
    """Cria as tabelas no banco de dados, se não existirem."""
    try:
        print("📦 Criando tabelas no banco de dados...")
        Base.metadata.create_all(bind=engine)
        print("✅ Banco de dados inicializado com sucesso!")
    except OperationalError as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        print("⚠️ Verifique se o MySQL está rodando e se as credenciais estão corretas.")

def get_db():
    """Cria uma sessão e garante que seja fechada corretamente."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
