from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# --- IMPORTAÇÕES CORRIGIDAS ---
from app.routers.auth import get_current_user_from_cookie 
from app.db.session import get_session
from app.services.lead_services import (
    start_and_persist_search,
    start_and_persist_mock_search,
)
from app.schemas.lead import StartSearchIn, StartSearchSummary
# ----------------------------

router = APIRouter(prefix="/search", tags=["search_api"])

# A rota /results que renderizava HTML foi removida,
# pois a rota /historico em auth.py já tem essa responsabilidade.

@router.post("/start", response_model=StartSearchSummary, status_code=status.HTTP_201_CREATED)
async def start_search(
    payload: StartSearchIn,
    session: AsyncSession = Depends(get_session),
    # --- DEPENDÊNCIA DE AUTENTICAÇÃO CORRIGIDA ---
    current_user=Depends(get_current_user_from_cookie),
):
    """
    Inicia a busca de leads (mock ou Apify) para o utilizador autenticado,
    persiste no banco e retorna um resumo.
    """
    try:
        if payload.use_mock:
            resumo = await start_and_persist_mock_search(
                session=session,
                user_id=current_user.id,
                sector=payload.sector,
                address=payload.address,
                radius_km=payload.radius_km,
                max_results=payload.max_results,
            )
        else:
            resumo = await start_and_persist_search(
                session=session,
                user_id=current_user.id,
                sector=payload.sector,
                address=payload.address,
                radius_km=payload.radius_km,
                max_results=payload.max_results,
            )
        return resumo 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao executar o serviço de scraping: {e}")

