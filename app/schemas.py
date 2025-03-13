from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


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

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str  # 🔹 Campo obrigatório para criação de usuários


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class TagBase(BaseModel):
    tag: str


class TagCreate(TagBase):
    movie_id: int
    user_id: Optional[int] = None


class TagResponse(TagBase):
    id: int
    movie_id: int
    user_id: Optional[int] = None
    timestamp: datetime  # 🔹 Garante compatibilidade com `DATETIME` no MySQL

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class MovieStatsResponse(BaseModel):
    total_movies: int
    total_ratings: int
    average_rating: Optional[float] = None
    top_genres: List[str]
