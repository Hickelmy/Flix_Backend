from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# 📌 1️⃣ - Esquemas para Filmes
class MovieBase(BaseModel):
    title: str
    year: Optional[int] = Field(None, ge=1888)  # O primeiro filme foi criado em 1888
    genres: Optional[str] = None


class MovieCreate(MovieBase):
    pass


class MovieResponse(MovieBase):
    id: int
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)  # Compatível com `DECIMAL(3,2)`
    image_base64: Optional[str] = None  # 🔹 Para armazenar imagens codificadas

    class Config:
        from_attributes = True  # Permite conversão automática de ORM


# 📌 2️⃣ - Esquemas para Usuários (Login)
class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str  # 🔹 Campo obrigatório para criação de usuários


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None  # 🔹 Permite atualização opcional da senha


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True  # Permite conversão automática de ORM


# 📌 3️⃣ - Esquemas para Avaliações (Ratings)
class RatingBase(BaseModel):
    rating: float = Field(..., ge=0.0, le=5.0)  # 🔹 Rating entre 0 e 5, compatível com `DECIMAL(3,2)`


class RatingCreate(RatingBase):
    movie_id: int
    user_id: Optional[int] = None


class RatingResponse(RatingBase):
    id: int
    movie_id: int
    user_id: Optional[int] = None
    timestamp: datetime  # 🔹 MySQL armazena como `DATETIME`

    class Config:
        from_attributes = True


# 📌 4️⃣ - Esquema para Token JWT (Autenticação)
class Token(BaseModel):
    access_token: str
    token_type: str


# 📌 5️⃣ - Estatísticas de Filmes
class MovieStatsResponse(BaseModel):
    total_movies: int
    total_ratings: int
    average_rating: Optional[float] = None
    top_genres: List[str]
