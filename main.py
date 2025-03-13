from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 🔹 Importar CORS Middleware
from fastapi.openapi.utils import get_openapi
import uvicorn

# 📌 Certifique-se de importar corretamente o router
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
        allow_origins=["*"],  # 🛑 Permitir todas as origens (pode restringir para "http://localhost:4200")
        allow_credentials=True,
        allow_methods=["*"],  # 🛑 Permitir todos os métodos (POST, GET, etc.)
        allow_headers=["*"],  # 🛑 Permitir todos os headers
    )
    # Incluindo os routers da API
    app.include_router(auth_router)  # 🔹 Sem prefixo duplicado
    app.include_router(router)

    return app




app = create_application()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
