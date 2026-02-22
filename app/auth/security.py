
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.user import User
from app.schemas.user import TokenData


SECRET_KEY: str = os.getenv("SECRET_KEY", "8hQz7tLp*kYf2b$JmXa9pW6sR4d@gV1eI0oU#cCbN5vF3qE") ## ou pega do secret_key
## ou por default podemos definir a chave secreta
ALGORITHM: str = "HS256" ## assinatura do JWT do token 
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
## mesmo conceito de secret_key

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
##funcao do fastapi para gerar o bearer token do usuario
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],  
    deprecated="auto",
)
## pwd_context eh a funcao de criptografia da senha com o deprecated em auto, significa que se mudarmos a logica no futuro
## ainda sim funcionara 

def get_password_hash(password: str) -> str:
    """Gera hash da senha com PBKDF2-SHA256."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica senha usando PBKDF2-SHA256."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um JWT assinado (HS256) contendo as claims de `data`.
    Inclua ao menos "sub" (email) e/ou "uid" (id do usuário).
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    """"
    pega um valor que o dev escolher ou o padrao do acesso_token 
    """
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def decode_token_to_data(token: str) -> TokenData:
    """
    Decodifica o token e retorna TokenData; lança 401 se inválido/expirado.
    """
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("uid")
        email = payload.get("sub")
        if user_id is None and email is None:
            raise cred_exc
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        raise cred_exc


async def authenticate_user(
    session: AsyncSession,
    email: EmailStr,
    password: str,
) -> Optional[User]:
    """
    Autentica por email/senha. Retorna User se ok; caso contrário, None.
    """
    stmt = select(User).where(User.email == str(email))
    result = await session.execute(stmt)
    user: Optional[User] = result.scalars().first()
    ## pega o primeiro resultado, normalmente esse resultado do banco de dados eh object, uso o scalars para transformar em biblioteca e depois pego o primeiro registro
    ## que seria o nome,user_id, senha e etc
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Lê o Bearer token, decodifica e retorna o usuário carregado do banco.
    Use: current_user: User = Depends(get_current_user)
    """
    token_data = await decode_token_to_data(token)

    user: Optional[User] = None
    if token_data.user_id is not None:
        result = await session.execute(select(User).where(User.id == token_data.user_id))
        user = result.scalars().first()
    elif token_data.email is not None:
        result = await session.execute(select(User).where(User.email == str(token_data.email)))
        user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def issue_access_token_for_user(user: User) -> str:
    """
    Gera e retorna um access_token JWT para o usuário informado.
    Inclui 'sub' (email) e 'uid' (id) como claims.
    """
    claims = {"sub": user.email, "uid": user.id}
    return create_access_token(data=claims)
