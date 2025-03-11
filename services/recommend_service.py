import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from app import models
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split

def get_movie_recommendations(movie_id: int, db: Session):
    """🔍 Retorna recomendações baseadas no conteúdo do filme."""
    movies = db.query(models.Movie).all()
    df = pd.DataFrame([{"id": m.id, "title": m.title, "genres": m.genres} for m in movies])

    if movie_id not in df["id"].values:
        return []

    tfidf = TfidfVectorizer(stop_words="english")
    tfidf_matrix = tfidf.fit_transform(df["genres"].fillna(""))

    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    idx = df.index[df["id"] == movie_id].tolist()[0]

    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]
    movie_indices = [i[0] for i in sim_scores]

    return df.iloc[movie_indices].to_dict(orient="records")

def train_collaborative_model(db: Session):
    ratings = db.query(models.Rating).all()
    df = pd.DataFrame([{"user_id": r.user_id, "movie_id": r.movie_id, "rating": r.rating} for r in ratings])

    if df.empty:
        return None

    reader = Reader(rating_scale=(0, 5))
    data = Dataset.load_from_df(df[["user_id", "movie_id", "rating"]], reader)
    trainset, _ = train_test_split(data, test_size=0.2)
    model = SVD()
    model.fit(trainset)

    return model

def get_user_recommendations(user_id: int, db: Session, model):
    movies = db.query(models.Movie).all()
    predictions = [(m.id, model.predict(user_id, m.id).est) for m in movies]
    predictions.sort(key=lambda x: x[1], reverse=True)
    return [{"id": movie_id, "title": db.query(models.Movie).filter(models.Movie.id == movie_id).first().title}
            for movie_id, _ in predictions[:5]]
