from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import register_user, authenticate_user
from schemas import UserCreate, UserLogin
from typing import Dict

auth_router = APIRouter()

@auth_router.post("/register", summary="Registrar novo usuário", response_model=Dict[str, str])
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Registra um novo usuário no sistema.

    - **email**: Endereço de e-mail do usuário
    - **password**: Senha do usuário (será armazenada de forma segura)
    """
    result = register_user(db, user)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@auth_router.post("/login", summary="Login do usuário", response_model=Dict[str, str])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Realiza login e retorna um token JWT válido.

    - **username**: Email do usuário
    - **password**: Senha do usuário
    """
    result = authenticate_user(db, form_data.username, form_data.password, False)
    if result is None:
        raise HTTPException(status_code=400, detail="Email ou senha inválidos")
    return result
