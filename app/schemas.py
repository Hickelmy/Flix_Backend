from pydantic import BaseModel, ConfigDict
from typing import Optional

### 📌 **Schemas para Filmes**
class MovieBase(BaseModel):
    title: str
    year: Optional[int] = None
    genres: Optional[str] = None

class MovieCreate(MovieBase):
    pass

class MovieResponse(MovieBase):
    id: int
    rating: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


### 📌 **Schemas para Usuários**
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


### 📌 **Schema para Tokens de Autenticação**
class Token(BaseModel):
    access_token: str
    token_type: str
