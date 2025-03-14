from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import pandas as pd
from pydantic import BaseModel
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import numpy as np
from scipy.sparse import csr_matrix
from app import models, schemas, database

router = APIRouter(prefix="/movies", tags=["Filmes"])

_model_cache = None
_user_movie_matrix = None
_scaler = StandardScaler()

class UserVote(BaseModel):
    user_id: int
    movie_id: int

def format_movie_response(movie: models.Movie, db: Session):
    return {
        "id": movie.id,
        "title": movie.title,
        "year": movie.year,
        "genres": movie.genres,
        "image_base64": movie.image_base64,
        "rating": movie.average_rating(db),
    }

@router.get("/", response_model=List[schemas.MovieResponse])
def get_movies(
    title: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    genres: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.Movie)
    
    if title:
        query = query.filter(models.Movie.title.ilike(f"%{title}%"))
    if year:
        query = query.filter(models.Movie.year == year)
    if genres:
        query = query.filter(models.Movie.genres.ilike(f"%{genres}%"))

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

@router.post("/like/")
def like_movie(data: UserVote, db: Session = Depends(database.get_db)):
    existing_like = db.query(models.Rating).filter(
        models.Rating.user_id == data.user_id,
        models.Rating.movie_id == data.movie_id
    ).first()

    if existing_like:
        return {"message": "Você já curtiu esse filme!"}

    db.add(models.Rating(user_id=data.user_id, movie_id=data.movie_id, rating=5))
    db.commit()

    return {"message": "Filme curtido com sucesso!"}

@router.post("/dislike/")
def dislike_movie(data: UserVote, db: Session = Depends(database.get_db)):
    db.add(models.Rating(user_id=data.user_id, movie_id=data.movie_id, rating=0))
    db.commit()
    return {"message": "Filme descurtido!"}

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
            func.coalesce(func.avg(models.Rating.rating), 0).desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not popular_movies:
        raise HTTPException(status_code=404, detail="Nenhum filme popular encontrado.")

    return [format_movie_response(movie, db) for movie in popular_movies]



def train_collaborative_model(db):
    ratings = db.query(models.Rating).all()

    if not ratings:
        return None  

    df = pd.DataFrame([(r.user_id, r.movie_id, r.rating) for r in ratings], 
                      columns=["user_id", "movie_id", "rating"])

    if df.empty or len(df["user_id"].unique()) < 2:
        return None  

    user_movie_matrix = df.pivot(index="user_id", columns="movie_id", values="rating").fillna(0)
    user_movie_matrix = user_movie_matrix.astype(np.float32)

    sparse_matrix = csr_matrix(user_movie_matrix)

    model = NearestNeighbors(metric="cosine", algorithm="brute")
    model.fit(sparse_matrix)

    return model, user_movie_matrix  

def recommend_by_genre(user_id: int, db: Session):
    last_liked_movie = (
        db.query(models.Rating)
        .filter(models.Rating.user_id == user_id)
        .order_by(models.Rating.id.desc())
        .first()
    )

    if not last_liked_movie:
        return []

    liked_movie = db.query(models.Movie).filter(models.Movie.id == last_liked_movie.movie_id).first()

    if not liked_movie:
        return []

    similar_movies = (
        db.query(models.Movie)
        .filter(models.Movie.genres.ilike(f"%{liked_movie.genres.split('|')[0]}%"))
        .limit(5)
        .all()
    )

    return similar_movies
@router.get("/recommend/{user_id}")
def recommend_movies(user_id: int, db: Session = Depends(database.get_db)):
    global _model_cache, _user_movie_matrix

    if _model_cache is None or _user_movie_matrix is None:
        result = train_collaborative_model(db)
        if result is None:
            return recommend_by_genre(user_id, db)  
        _model_cache, _user_movie_matrix = result  

    liked_movies = db.query(models.Rating.movie_id).filter(
        models.Rating.user_id == user_id,
        models.Rating.rating == 5
    ).all()

    if not liked_movies:
        return recommend_by_genre(user_id, db)  

    liked_movie_ids = {movie.movie_id for movie in liked_movies}  

    if user_id not in _user_movie_matrix.index:
        return recommend_by_genre(user_id, db)  

    user_index = list(_user_movie_matrix.index).index(user_id)
    distances, indices = _model_cache.kneighbors([_user_movie_matrix.iloc[user_index]], n_neighbors=5)

    similar_users = _user_movie_matrix.iloc[indices[0][1:]].mean()
    recommended_movie_ids = [m for m in similar_users.sort_values(ascending=False).index.tolist() if m not in liked_movie_ids][:5]  

    recommended_movies = db.query(models.Movie).filter(models.Movie.id.in_(recommended_movie_ids)).limit(5).all()

    if not recommended_movies:
        return recommend_by_genre(user_id, db)  

    return [
        {
            "id": movie.id,
            "title": movie.title,
            "year": movie.year,
            "genres": movie.genres,
            "image_base64": movie.image_base64,
            "tmdb_image": movie.tmdb_image
        }
        for movie in recommended_movies
    ]