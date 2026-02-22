from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

from app.db.session import create_all
from app.routers import auth, leads

# --- Configuração da Aplicação ---
APP_TITLE = os.getenv("APP_TITLE", "GeraLead – Backend")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "false").lower() in {"1", "true", "yes"}

# --- Configuração do CORS ---
# Permite que o frontend (rodando em outra porta/domínio) se comunique com o backend
_ORIGINS = os.getenv("CORS_ORIGINS", "*")
ORIGINS = ["*"] if _ORIGINS.strip() == "*" else [o.strip() for o in _ORIGINS.split(",") if o.strip()]

# --- Inicialização do FastAPI ---
app = FastAPI(title=APP_TITLE, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuração de Arquivos Estáticos (CSS, JS, Imagens) ---
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- Inclusão dos Roteadores ---
app.include_router(auth.router)
app.include_router(leads.router)


# --- Eventos de Startup ---
@app.on_event("startup")
async def on_startup() -> None:
    """Cria as tabelas no banco de dados na inicialização, se configurado."""
    if AUTO_CREATE_TABLES:
        await create_all()


# --- Rota Principal (Health Check) ---
@app.get("/", tags=["health"])
async def root():
    """Rota raiz para verificar se a API está funcionando."""
    return {"ok": True, "name": APP_TITLE, "version": APP_VERSION}

# ROTA /home E FUNÇÃO _load_user_from_cookie REMOVIDAS DAQUI.
# A rota /home agora é gerenciada exclusivamente pelo roteador em app/routers/auth.py,
# que é a abordagem correta para organizar o projeto.

