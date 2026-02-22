from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# ---------- Entrada para iniciar busca ----------
class StartSearchIn(BaseModel):
    sector: str = Field(..., description="Ex.: 'restaurantes'")
    address: str = Field(..., description="Cidade ou endereço")
    radius_km: float = Field(..., gt=0, le=50, description="Raio em km (até 50)")
    max_results: int = Field(100, ge=1, le=1000, description="Quantidade desejada (1–1000).")
    use_mock: bool = Field(
        default=True,
        description="Se true, gera dados fictícios (mock) sem chamadas externas.",
    )

# ---------- Resumo ao iniciar ----------
class StartSearchSummary(BaseModel):
    search_id: int               # id do LeadSearch criado
    dataset_id: str
    total_coletado: int
    inseridos: int
    ignorados_por_conflito: int

# ---------- Histórico: uma busca (Lead #N) ----------
class SearchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int                           # usado como "Lead #id"
    user_id: int
    query: str                        # termo digitado (ou use 'term' se seu modelo usa esse nome)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    results_count: int

# ---------- Resultados de uma busca ----------
class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    search_id: int
    place_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    opening_hours: Optional[Any] = None
    website: Optional[str] = None
    url: Optional[str] = None
    source_id: Optional[str] = None    # se existir no modelo
    # se você tiver mais campos (ex.: category/site), adicione aqui:
    # category: Optional[str] = None
    # site: Optional[str] = None

