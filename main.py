from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from database import engine, Base
from routers.auth_routes import auth_router  

app = FastAPI(
    title="LGFlix API",
    description="API para gerenciamento de usuários e filmes",
    version="1.0.0",
    docs_url="/docs",  
    redoc_url="/redoc",  
    openapi_url="/openapi.json"  
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router, prefix="/auth", tags=["Autenticação"])

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="ManausFlix API",
        version="1.0.0",
        description="API para autenticação e gerenciamento de usuários/filmes",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi  

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005, reload=True)
