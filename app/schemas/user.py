from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from fastapi import Form

# ---------- Inputs de formulário ----------
class UserCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    cpf: Optional[str] = Field(None, max_length=14)
    phone: Optional[str] = Field(None, max_length=32)

    @classmethod
    def as_form(
        cls,
        nome: str = Form(..., min_length=2, max_length=120),
        email: EmailStr = Form(...),
        password: str = Form(..., min_length=8, max_length=72),
        cpf: Optional[str] = Form(None, max_length=14),
        phone: Optional[str] = Form(None, max_length=32),
    ) -> "UserCreate":
        return cls(nome=nome, email=email, password=password, cpf=cpf, phone=phone)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

    @classmethod
    def as_form(
        cls,
        email: EmailStr = Form(...),
        password: str = Form(..., min_length=8, max_length=72),
    ) -> "UserLogin":
        return cls(email=email, password=password)

# ---------- Atualização de perfil ----------
class UserUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=120)
    cpf: Optional[str] = Field(None, max_length=14)
    phone: Optional[str] = Field(None, max_length=32)

# ---------- Saídas ----------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    email: EmailStr
    cpf: Optional[str] = None
    phone: Optional[str] = None
    role: str                     # 👈 expõe o papel ("user" | "admin")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None    # opcional; só use se também incluir no JWT
