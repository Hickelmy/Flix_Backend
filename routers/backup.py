from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Movie, Rating
from app.schemas import MovieResponse
from typing import List

movies_router = APIRouter()

@movies_router.get("/", response_model=List[MovieResponse])
def get_movies(title: str = None, year: int = None, genre: str = None, db: Session = Depends(get_db)):
    query = db.query(Movie)

    if title:
        query = query.filter(Movie.title.ilike(f"%{title}%"))  
    if year:
        query = query.filter(Movie.year == year)
    if genre:
        query = query.filter(Movie.genres.ilike(f"%{genre}%"))

    movies = query.limit(50).all() 
    return movies

@movies_router.get("/top", response_model=List[MovieResponse])
def get_top_movies(limit: int = 10, db: Session = Depends(get_db)):
    top_movies = db.query(Movie).join(Rating).group_by(Movie.id).order_by(Rating.rating.desc()).limit(limit).all()
    
    if not top_movies:
        raise HTTPException(status_code=404, detail="Nenhum filme encontrado")
    
    return top_movies
