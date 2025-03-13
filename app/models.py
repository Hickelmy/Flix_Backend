from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship
from app.database import Base, engine

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    year = Column(Integer, nullable=True)
    genres = Column(String, nullable=True)
    image_base64 = Column(Text, nullable=True)  # Armazena a imagem em Base64

    ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="movie", cascade="all, delete-orphan")

    def average_rating(self, session):
        avg_rating = session.query(func.avg(Rating.rating)).filter(Rating.movie_id == self.id).scalar()
        print(avg_rating)
        return round(avg_rating, 2) if avg_rating else None


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  
    rating = Column(Float(precision=2), nullable=False)  # 🔹 Garante precisão decimal correta
    timestamp = Column(DateTime, nullable=False, default=func.now())  # 🔹 Garantia de timestamp correto

    movie = relationship("Movie", back_populates="ratings")
    user = relationship("User", back_populates="ratings", lazy="joined")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  
    tag = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=func.now())  # 🔹 Garantia de timestamp correto

    movie = relationship("Movie", back_populates="tags")
    user = relationship("User", back_populates="tags", lazy="joined")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  

    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="user", cascade="all, delete-orphan")


# 📌 Criar as tabelas automaticamente caso o script seja executado diretamente
if __name__ == "__main__":
    print("📦 Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados atualizado com sucesso!")