from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
import uvicorn

# 📌 Certifique-se de importar corretamente o router
from routers.auth_routes import auth_router
from routers.movies_routes import movies_router


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

    # Incluindo os routers da API
    app.include_router(auth_router)  # 🔹 Sem prefixo duplicado
    app.include_router(movies_router)

    return app


app = create_application()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3005, reload=True)
