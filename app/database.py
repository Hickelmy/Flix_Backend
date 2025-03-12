import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./movielens_1m.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

class Base(DeclarativeBase):
    pass

def init_db():
    print("📦 Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados inicializado com sucesso!")

def get_db():
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
