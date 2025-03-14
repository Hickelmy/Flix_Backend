import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "movielens")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()


def check_and_create_tables():
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        required_tables = [table.__tablename__ for table in Base.__subclasses__()]

        missing_tables = [table for table in required_tables if table not in existing_tables]

        if missing_tables:
            print(f"📌 Criando tabelas ausentes: {missing_tables}")
            Base.metadata.create_all(bind=engine)
            print("✅ Todas as tabelas foram criadas com sucesso!")
        else:
            print("✔️ Todas as tabelas já existem. Nenhuma alteração necessária.")

    except SQLAlchemyError as e:
        print(f"❌ Erro ao verificar/criar tabelas: {str(e)}")


def test_database_connection():
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")  # Testa a conexão
        print("✅ Conexão com o banco de dados bem-sucedida!")
    except OperationalError as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")
        print("⚠️ Verifique se o MySQL está rodando e se as credenciais estão corretas.")


def init_db():
    test_database_connection()
    check_and_create_tables()


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
    init_db()  # 🚀 Inicializa o banco ao rodar diretamente o script
