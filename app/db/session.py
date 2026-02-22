import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:1234@localhost:5432/geralead",
)
if not DATABASE_URL or not DATABASE_URL.strip():
    raise RuntimeError("DATABASE_URL não configurado no .env")
## strip remove espacoes em branco
engine = create_async_engine(
    DATABASE_URL,
    echo=False,          
    pool_pre_ping=True,
)
## o engine gerencia a conexao com o banco de dados, no nosso caso o postgree utilizando o asyncpg
## por isso todas as funcoes sao async como solicitado na documentacao 
## para aparecer as queries geradas no log coloquei em off para nao poluir o log
## garante que conexoes velhas sejam testadas antes de usar
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    
)
## o engine eh o motor e a sessionmaker eh a fabrica que lhe da sessao para conectar com o banco
## dados continuam na memoria com expire_on_commit = False 

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session  
## fastAPI usa yield nas dependencias para gerenciar recursos que precisam ser abertos e fechados

async def create_all() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
## SQLAlchemy nasceu sincrono, muitas funcoes como create_all sao sincronos
## 

        
