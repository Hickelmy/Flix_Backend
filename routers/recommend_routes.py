from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import database
from services.recommend_service import get_movie_recommendations, get_user_recommendations, train_collaborative_model

recommender_router = APIRouter(prefix="/recommend", tags=["Recomendações"])
model_cache = None  

@recommender_router.get("/{movie_id}")
def recommend_movies(movie_id: int, db: Session = Depends(database.get_db)):
    recommendations = get_movie_recommendations(movie_id, db)
    if not recommendations:
        raise HTTPException(status_code=404, detail="Nenhuma recomendação encontrada.")
    return {"recommendations": recommendations}

@recommender_router.get("/user/{user_id}")
def recommend_for_user(user_id: int, db: Session = Depends(database.get_db)):
    global model_cache
    if model_cache is None:
        model_cache = train_collaborative_model(db)
    if model_cache is None:
        raise HTTPException(status_code=400, detail="Não há avaliações suficientes para gerar recomendações.")

    recommendations = get_user_recommendations(user_id, db, model_cache)
    return {"user_id": user_id, "recommendations": recommendations}
