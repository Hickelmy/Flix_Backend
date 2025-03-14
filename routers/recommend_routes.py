from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import database
from services.recommend_service import (
    get_movie_recommendations,
    get_user_recommendations,
    train_collaborative_model
)

# 🔹 Configuração do Router
recommender_router = APIRouter(prefix="/recommend", tags=["Recomendações"])

# 🔹 Cache do modelo colaborativo (evita recomputação desnecessária)
_model_cache = None

def get_model_cache(db: Session):
    """Garante que o modelo colaborativo seja treinado apenas uma vez."""
    global _model_cache
    if _model_cache is None:
        _model_cache = train_collaborative_model(db)
        if _model_cache is None:
            raise HTTPException(status_code=400, detail="Não há avaliações suficientes para gerar recomendações.")
    return _model_cache

@recommender_router.get("/{movie_id}")
def recommend_movies(movie_id: int, db: Session = Depends(database.get_db)):
    """Recomenda filmes com base em um filme específico."""
    recommendations = get_movie_recommendations(movie_id, db)
    if not recommendations:
        raise HTTPException(status_code=404, detail="Nenhuma recomendação encontrada.")
    return {"movie_id": movie_id, "recommendations": recommendations}

@recommender_router.get("/user/{user_id}")
def recommend_for_user(user_id: int, db: Session = Depends(database.get_db)):
    """Recomenda filmes personalizados para um usuário baseado no modelo colaborativo."""
    model_cache = get_model_cache(db)
    recommendations = get_user_recommendations(user_id, db, model_cache)
    return {"user_id": user_id, "recommendations": recommendations}
