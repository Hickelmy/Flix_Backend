from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

from app import models, database
from app.schemas import UserCreate, UserLogin, UserResponse, Token

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Contexto para criptografia de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependência para autenticação via JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Inicialização do roteador
auth_router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Função para criar um token JWT
def create_access_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Função para obter usuário autenticado
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.Login).filter(models.Login.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Rota para registrar usuário na tabela `login`
@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(database.get_db)):
    existing_user = db.query(models.Login).filter(models.Login.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário já existe!")

    hashed_password = pwd_context.hash(user.password)
    new_user = models.Login(username=user.username, password_hash=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# Rota para login e geração de token JWT
@auth_router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(database.get_db)):
    db_user = db.query(models.Login).filter(models.Login.username == user.username).first()

    if not db_user or not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas!")

    token = create_access_token(db_user.username)
    return {"access_token": token, "token_type": "bearer"}

# Rota para obter dados do usuário autenticado
@auth_router.get("/me", response_model=UserResponse)
def get_me(current_user: models.Login = Depends(get_current_user)):
    return current_user
