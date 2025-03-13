from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app import models, schemas, database

router = APIRouter(prefix="/movies", tags=["Filmes"])

def format_movie_response(movie: models.Movie, db: Session):
    return {
        "id": movie.id,
        "title": movie.title,
        "year": movie.year,
        "genres": movie.genres,
        "image_base64": movie.image_base64,
        "rating": movie.average_rating(db)
    }

# 🔹 1. Buscar filmes por título
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

# 🔹 2. Buscar filme por ID
@router.get("/{movie_id}", response_model=schemas.MovieResponse)
def get_movie(movie_id: int, db: Session = Depends(database.get_db)):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail=f"Filme com ID {movie_id} não encontrado.")

    return format_movie_response(movie, db)

# 🔹 3. Buscar filmes por ano e gênero
@router.get("/search/", response_model=List[schemas.MovieResponse])
def search_movies(
    year: int,
    genre: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.Movie).filter(
        models.Movie.year == year,
        models.Movie.genres.ilike(f"%{genre}%")
    )

    movies = query.offset(offset).limit(limit).all()

    if not movies:
        raise HTTPException(status_code=404, detail="Nenhum filme encontrado.")

    return [format_movie_response(movie, db) for movie in movies]

# 🔹 4. Listar os filmes mais bem avaliados
@router.get("/top-movies/", response_model=List[schemas.MovieResponse])
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

# 🔹 5. Filmes populares (baseado na quantidade de avaliações e notas)
@router.get("/popular-movies/", response_model=List[schemas.MovieResponse])
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

# 🔹 6. Filmes em alta (Trending Now) - Mais avaliados recentemente
@router.get("/trending-now/", response_model=List[schemas.MovieResponse])
def get_trending_now(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(database.get_db),
):
    trending_movies = (
        db.query(models.Movie)
        .join(models.Rating)
        .group_by(models.Movie.id)
        .order_by(func.max(models.Rating.timestamp).desc())
        .limit(limit)
        .all()
    )

    if not trending_movies:
        raise HTTPException(status_code=404, detail="Nenhum filme em alta encontrado.")

    return [format_movie_response(movie, db) for movie in trending_movies]

# 🔹 7. Séries de TV (TV Shows)
@router.get("/tv-shows/", response_model=List[schemas.MovieResponse])
def get_tv_shows(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(database.get_db),
):
    tv_shows = (
        db.query(models.Movie)
        .filter(models.Movie.genres.ilike("%TV Show%"))
        .limit(limit)
        .all()
    )

    if not tv_shows:
        raise HTTPException(status_code=404, detail="Nenhuma série de TV encontrada.")

    return [format_movie_response(movie, db) for movie in tv_shows]

# 🔹 8. Filmes de Ação & Aventura (Action & Adventure)
@router.get("/action-adventure/", response_model=List[schemas.MovieResponse])
def get_action_adventure(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(database.get_db),
):
    action_movies = (
        db.query(models.Movie)
        .filter(models.Movie.genres.ilike("%Action%"), models.Movie.genres.ilike("%Adventure%"))
        .limit(limit)
        .all()
    )

    if not action_movies:
        raise HTTPException(status_code=404, detail="Nenhum filme de ação e aventura encontrado.")

    return [format_movie_response(movie, db) for movie in action_movies]

# 🔹 9. Estatísticas gerais dos filmes
@router.get("/stats/", response_model=schemas.MovieStatsResponse)
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
