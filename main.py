from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 🔹 Importar CORS Middleware
from fastapi.openapi.utils import get_openapi
import uvicorn

from routers.auth_routes import auth_router
from routers.movies_routes import  router


def create_application() -> FastAPI:
    """Cria e configura a aplicação FastAPI."""
    app = FastAPI(
        title="Flix API",
        description="API para gerenciamento de usuários e filmes",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  
        allow_credentials=True,
        allow_methods=["*"],  
        allow_headers=["*"],
    )
    app.include_router(auth_router)  
    app.include_router(router)

    return app




app = create_application()

if __name__ == "__main__":
    uvicorn.run("main:app",  port=8000, reload=True)
