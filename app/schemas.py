from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MovieBase(BaseModel):
    title: str
    year: Optional[int] = Field(None, ge=1888)
    genres: Optional[str] = None

class MovieCreate(MovieBase):
    pass

class MovieResponse(MovieBase):
    id: int
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    image_base64: Optional[str] = None

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class RatingBase(BaseModel):
    rating: float = Field(..., ge=0.0, le=5.0)

class RatingCreate(RatingBase):
    movie_id: int
    user_id: Optional[int] = None

class RatingResponse(RatingBase):
    id: int
    movie_id: int
    user_id: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class MovieStatsResponse(BaseModel):
    total_movies: int
    total_ratings: int
    average_rating: Optional[float] = None
    top_genres: List[str]
