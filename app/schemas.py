from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class MovieBase(BaseModel):
    title: str
    year: Optional[int] = None
    genres: Optional[str] = None


class MovieCreate(MovieBase):
    pass


class MovieResponse(MovieBase):
    id: int
    rating: Optional[float] = None
    image_base64: Optional[str] = None 

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RatingBase(BaseModel):
    rating: float


class RatingCreate(RatingBase):
    movie_id: int
    user_id: Optional[int] = None


class RatingResponse(RatingBase):
    id: int
    movie_id: int
    user_id: Optional[int] = None
    timestamp: datetime

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
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class MovieStatsResponse(BaseModel):
    total_movies: int
    total_ratings: int
    average_rating: Optional[float] = None
    top_genres: List[str]
