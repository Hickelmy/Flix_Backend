from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship
from app.database import Base, engine


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    year = Column(Integer, nullable=True)
    genres = Column(String, nullable=True)
    image_base64 = Column(Text, nullable=True)  # Armazena a URL da imagem

    ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan", lazy="joined")

    def average_rating(self, session):
        avg_rating = session.query(func.avg(Rating.rating)).filter(Rating.movie_id == self.id).scalar()
        return round(avg_rating, 2) if avg_rating else 0.0  # Retorna 0.0 ao invés de None

    def __repr__(self):
        return f"<Movie(id={self.id}, title={self.title}, year={self.year})>"


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  
    rating = Column(Float(precision=2), nullable=False)  # 🔹 Garante precisão decimal correta
    timestamp = Column(DateTime, nullable=False, default=func.now())  # 🔹 Garantia de timestamp correto

    movie = relationship("Movie", back_populates="ratings", lazy="joined")
    user = relationship("User", back_populates="ratings", lazy="joined")

    def __repr__(self):
        return f"<Rating(user_id={self.user_id}, movie_id={self.movie_id}, rating={self.rating})>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    gender = Column(String(10), nullable=False)
    age = Column(Integer, nullable=False)
    occupation = Column(Integer, nullable=False)
    zip_code = Column(String(20), nullable=False)

    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan", lazy="joined")



class Login(Base):
    __tablename__ = "login"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)



# 📌 Criar as tabelas automaticamente caso o script seja executado diretamente
if __name__ == "__main__":
    print("📦 Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados atualizado com sucesso!")
