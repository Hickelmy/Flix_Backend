from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app import models, schemas, database

router = APIRouter(prefix="/movies", tags=["Filmes"])


def format_movie_response(movie: models.Movie, db: Session):
    """
    Retorna um dicionário formatado para um filme específico.
    """
    return {
        "id": movie.id,
        "title": movie.title,
        "year": movie.year,
        "genres": movie.genres,
        "image_base64": movie.image_base64,
        "rating": movie.average_rating(db)  # Calcula a média de avaliação
    }


# 🔹 1️⃣ Buscar filmes por título, ano ou gênero
@router.get("/", response_model=List[schemas.MovieResponse])
def get_movies(
    title: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    genres: Optional[str] = Query(None),  # Alterado para "genres" em vez de "genre"
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.Movie)

    if title:
        query = query.filter(models.Movie.title.ilike(f"%{title}%"))
    if year:
        query = query.filter(models.Movie.year == year)
    if genres:  # Alterado aqui
        query = query.filter(models.Movie.genres.ilike(f"%{genres}%"))  # Alterado aqui

    movies = query.offset(offset).limit(limit).all()

    if not movies:
        raise HTTPException(status_code=404, detail="Nenhum filme encontrado.")

    return [format_movie_response(movie, db) for movie in movies]



# 🔹 2️⃣ Buscar filme por ID
@router.get("/{movie_id}", response_model=schemas.MovieResponse)
def get_movie(movie_id: int, db: Session = Depends(database.get_db)):
    """
    Retorna um filme específico pelo ID.
    """
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail=f"Filme com ID {movie_id} não encontrado.")

    return format_movie_response(movie, db)


# 🔹 3️⃣ Buscar filmes mais bem avaliados
@router.get("/top-movies/", response_model=List[schemas.MovieResponse])
def get_top_movies(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
):
    """
    Retorna os filmes mais bem avaliados.
    """
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


# 🔹 4️⃣ Buscar filmes populares (mais avaliados)
@router.get("/popular-movies/", response_model=List[schemas.MovieResponse])
def get_popular_movies(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
):
    """
    Retorna os filmes mais populares baseados no número de avaliações.
    """
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


# 🔹 5️⃣ Buscar filmes em alta (Trending Now)
@router.get("/trending-now/", response_model=List[schemas.MovieResponse])
def get_trending_now(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(database.get_db),
):
    """
    Retorna os filmes mais recentes com avaliações.
    """
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


# 🔹 6️⃣ Estatísticas gerais dos filmes
@router.get("/stats/", response_model=schemas.MovieStatsResponse)
def get_movies_stats(db: Session = Depends(database.get_db)):
    """
    Retorna estatísticas gerais do banco de filmes.
    """
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
