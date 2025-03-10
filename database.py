from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./users.db"

# Para conectar com o Azure, altere a variável DATABASE_URL para o seu banco na nuvem.
# Exemplo:
# DATABASE_URL = "mssql+pyodbc://usuario:senha@servidor.database.windows.net/nome_do_banco?driver=ODBC+Driver+17+for+SQL+Server"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
