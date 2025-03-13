import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase

# Configuração do MySQL
DB_USER = os.getenv("DB_USER", "root")  # Usuário padrão do MySQL
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")  # Senha definida no MySQL
DB_HOST = os.getenv("DB_HOST", "localhost")  # Pode ser "mysql" se estiver rodando dentro do Docker Compose
DB_PORT = os.getenv("DB_PORT", "3306")  # Porta padrão do MySQL
DB_NAME = os.getenv("DB_NAME", "movielens")

# String de conexão para MySQL
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Criando o motor de conexão com MySQL
engine = create_engine(DATABASE_URL, echo=False)

# Criando a sessão do banco de dados
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

class Base(DeclarativeBase):
    pass

def init_db():
    """Cria as tabelas no banco de dados."""
    print("📦 Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados inicializado com sucesso!")

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
