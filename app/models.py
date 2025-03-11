from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from app.database import engine

Base = declarative_base()

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    year = Column(Integer, nullable=True)
    genres = Column(String, nullable=True)

    ratings = relationship("Rating", back_populates="movie", cascade="all, delete")
    tags = relationship("Tag", back_populates="movie", cascade="all, delete")

    def average_rating(self):
        if not self.ratings:
            return None 
        return sum(r.rating for r in self.ratings) / len(self.ratings)


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False)

    movie = relationship("Movie", back_populates="ratings")
    user = relationship("User", back_populates="ratings")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String, nullable=False)

    movie = relationship("Movie", back_populates="tags")
    user = relationship("User", back_populates="tags")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    ratings = relationship("Rating", back_populates="user", cascade="all, delete")
    tags = relationship("Tag", back_populates="user", cascade="all, delete")


Base.metadata.create_all(bind=engine)
