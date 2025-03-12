from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app import models, schemas, database

router = APIRouter(prefix="/movies", tags=["Filmes"])

IMAGE_BASE_URL = "https://localhost/images/"

def format_movie_response(movie: models.Movie, db: Session):
    return {
        **movie.__dict__,
        "image_url": f"{IMAGE_BASE_URL}{movie.id}.jpg" if movie.image_base64 else None,
        "rating": movie.average_rating(db)
    }

@router.get("/", response_model=List[schemas.MovieResponse])
def get_movies(
    title: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    genre: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.Movie)

    if title:
        query = query.filter(models.Movie.title.ilike(f"%{title}%"))
    if year:
        query = query.filter(models.Movie.year == year)
    if genre:
        query = query.filter(models.Movie.genres.ilike(f"%{genre}%"))

    movies = query.offset(offset).limit(limit).all()

    if not movies:
        raise HTTPException(status_code=404, detail="Nenhum filme encontrado.")

    return [format_movie_response(movie, db) for movie in movies]

@router.get("/{movie_id}", response_model=schemas.MovieResponse)
def get_movie(movie_id: int, db: Session = Depends(database.get_db)):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail=f"Filme com ID {movie_id} não encontrado.")

    return format_movie_response(movie, db)

@router.get("/top", response_model=List[schemas.MovieResponse])
def get_top_movies(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
):
    top_movies = (
        db.query(models.Movie)
        .join(models.Rating)
        .group_by(models.Movie.id)
        .order_by(func.coalesce(func.avg(models.Rating.rating), 0).desc())  
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not top_movies:
        raise HTTPException(status_code=404, detail="Nenhum filme com avaliações encontrado.")

    return [format_movie_response(movie, db) for movie in top_movies]

@router.get("/latest", response_model=List[schemas.MovieResponse])
def get_latest_movies(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
):
    latest_movies = (
        db.query(models.Movie)
        .filter(models.Movie.year.isnot(None))  
        .order_by(models.Movie.year.desc()) 
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not latest_movies:
        raise HTTPException(status_code=404, detail="Nenhum filme recente encontrado.")

    return [format_movie_response(movie, db) for movie in latest_movies]

@router.get("/popular", response_model=List[schemas.MovieResponse])
def get_popular_movies(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
):
    popular_movies = (
        db.query(models.Movie)
        .join(models.Rating)
        .group_by(models.Movie.id)
        .order_by(
            func.count(models.Rating.id).desc(), 
            func.coalesce(func.avg(models.Rating.rating), 0).desc() 
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not popular_movies:
        raise HTTPException(status_code=404, detail="Nenhum filme popular encontrado.")

    return [format_movie_response(movie, db) for movie in popular_movies]

@router.get("/stats", response_model=schemas.MovieStatsResponse)
def get_movies_stats(db: Session = Depends(database.get_db)):
    total_movies = db.query(models.Movie).count()
    total_ratings = db.query(models.Rating).count()
    avg_rating = db.query(func.avg(models.Rating.rating)).scalar()
    most_popular_genres = (
        db.query(models.Movie.genres, func.count(models.Movie.id))
        .group_by(models.Movie.genres)
        .order_by(func.count(models.Movie.id).desc())
        .limit(5)
        .all()
    )

    return {
        "total_movies": total_movies,
        "total_ratings": total_ratings,
        "average_rating": round(avg_rating, 2) if avg_rating else None,
        "top_genres": [genre for genre, count in most_popular_genres]
    }
