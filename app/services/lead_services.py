# app/services/lead_services.py
from __future__ import annotations

import asyncio
import random
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Tuple, Sequence, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.apify_sdk import make_client, APIFY_ACTOR_ID
from app.geo import geocode
from app.models.lead_search import LeadSearch
from app.models.lead_result import LeadResult

# --- helpers de horário ---

WEEK_ORDER = [
    "segunda-feira","terça-feira","quarta-feira",
    "quinta-feira","sexta-feira","sábado","domingo"
]

def _norm_day_name(s: str) -> str:
    # normaliza para pt-br minúsculo (ajuda quando o Apify vem em inglês)
    s = (s or "").strip().lower()
    subs = {
        "monday":"segunda-feira","tuesday":"terça-feira","wednesday":"quarta-feira",
        "thursday":"quinta-feira","friday":"sexta-feira","saturday":"sábado","sunday":"domingo",
        "segunda":"segunda-feira","terça":"terça-feira","terca":"terça-feira","quarta":"quarta-feira",
        "quinta":"quinta-feira","sexta":"sexta-feira","sabado":"sábado","domingo":"domingo",
    }
    return subs.get(s, s)

def normalize_opening_hours(item: dict) -> list[dict] | None:
    """
    Tenta extrair e normalizar horários como:
    [{"day": "segunda-feira", "hours": "08:00–18:00"}, ...]
    Aceita campos comuns do Apify: openingHours, openingHoursText, hours, timetable etc.
    """
    raw = (
        item.get("openingHours")
        or item.get("openingHoursText")
        or item.get("hours")
        or item.get("timetable")
    )
    if not raw:
        return None

    rows: list[dict] = []

    # formatos mais comuns: lista de dicts ou lista de strings
    if isinstance(raw, list):
        for r in raw:
            if isinstance(r, dict):
                day = _norm_day_name(r.get("day") or r.get("name") or r.get("weekday") or "")
                hours = (r.get("hours") or r.get("text") or r.get("value") or "").strip()
            else:
                # string tipo "Monday: 08:00–18:00"
                parts = str(r).split(": ", 1)
                day = _norm_day_name(parts[0]) if parts else ""
                hours = parts[1] if len(parts) > 1 else ""
            if day and hours:
                rows.append({"day": day, "hours": hours})

    elif isinstance(raw, dict):
        # dict tipo {"monday": "08:00–18:00", ...}
        for k, v in raw.items():
            day = _norm_day_name(k)
            hours = str(v).strip()
            if day and hours:
                rows.append({"day": day, "hours": hours})

    if not rows:
        return None

    # ordena conforme a semana
    order = {d:i for i,d in enumerate(WEEK_ORDER)}
    rows.sort(key=lambda r: order.get(r["day"], 99))
    return rows


# -------------------- helpers de tipos/parse --------------------

def _to_int(v: Any) -> Optional[int]:
    if v is None:
        return None
    try:
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            s = s.replace(",", ".")
            return int(float(s))
        return int(v)
    except (ValueError, TypeError):
        return None

def _to_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            s = s.replace(",", ".")
            return float(s)
        return float(v)
    except (ValueError, TypeError):
        return None

# -------------------- helpers genéricos --------------------

def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(int(n), hi))

def _truncate(val: str | None, max_len: int) -> str | None:
    if val is None:
        return None
    s = str(val)
    return s if len(s) <= max_len else s[:max_len]

def build_run_input(sector: str, lat: float, lng: float, radius_km: float, max_results: int) -> dict:
    max_results = _clamp(max_results, 1, 1000)
    return {
        "searchStringsArray": [sector],
        "customGeolocation": {"type": "Point", "coordinates": [lng, lat], "radiusKm": radius_km},
        "maxCrawledPlacesPerSearch": max_results,
        "language": "pt-BR",
        "skipClosedPlaces": True,
    }

def _compose_address(item: Dict[str, Any]) -> str | None:
    addr_raw = item.get("address")
    if isinstance(addr_raw, str):
        return addr_raw
    if isinstance(addr_raw, dict):
        parts = [
            addr_raw.get("streetAddress") or addr_raw.get("street"),
            addr_raw.get("locality") or addr_raw.get("city"),
            addr_raw.get("state"),
        ]
        parts = [p for p in parts if p]
        return ", ".join(parts) if parts else None
    parts = [
        item.get("streetAddress") or item.get("street"),
        item.get("city"),
        item.get("state"),
    ]
    parts = [p for p in parts if p]
    return ", ".join(parts) if parts else None

def map_apify_item_to_result_row(item: Dict[str, Any], search_id: int) -> Dict[str, Any]:
    fallback_url = item.get("url") or item.get("link") or item.get("placeUrl") or item.get("googleMapsUrl")
    return {
        "search_id": search_id,
        "place_name": _truncate(item.get("placeName") or item.get("title") or item.get("name"), 255),
        "address": _truncate(_compose_address(item), 255),
        "phone": _truncate(item.get("phone") or item.get("formattedPhoneNumber"), 64),
        "rating": _to_float(item.get("totalScore")) or _to_float(item.get("rating")),
        "reviews_count": _to_int(item.get("reviewsCount")) or _to_int(item.get("reviews")),
        "website": _truncate(
            item.get("website")
            or item.get("site")
            or item.get("facebookPageUrl")
            or item.get("instagramPageUrl")
            or item.get("twitterPageUrl"),
            512
        ),
        "url": _truncate(fallback_url, 1024),
        "source_id": _truncate(
            item.get("placeId")
            or item.get("googleId")
            or item.get("cid")
            or fallback_url,
            128,
        ),
        "opening_hours": normalize_opening_hours(item), 
        # se tiver mais campos no modelo, acrescente aqui (ex.: category/site)
    }

# -------------------- mock data --------------------

MOCK_NAME_PREFIXES = [
    "Atlas", "Brisa", "Nexo", "Solar", "Ponto", "Viva", "Orbe", "Prime", "Aurora", "Norte"
]

MOCK_NAME_SUFFIXES = [
    "Central", "Conecta", "Express", "Hub", "Plus", "Studio", "Pro", "Master", "Flow", "Select"
]

MOCK_STREETS = [
    "das Acacias", "do Comercio", "da Estacao", "dos Navegantes", "dos Girassois",
    "da Inovacao", "dos Pioneiros", "das Palmeiras", "da Praca", "dos Jasmins"
]

MOCK_NEIGHBORHOODS = [
    "Centro", "Nova Esperanca", "Horizonte", "Jardim Azul", "Lagoa Nova", "Bela Vista"
]

MOCK_HOURS_TEMPLATES: list[dict[str, str]] = [
    {
        "monday": "08:00-18:00",
        "tuesday": "08:00-18:00",
        "wednesday": "08:00-18:00",
        "thursday": "08:00-18:00",
        "friday": "08:00-18:00",
        "saturday": "08:00-13:00",
        "sunday": "Fechado",
    },
    {
        "monday": "09:00-19:00",
        "tuesday": "09:00-19:00",
        "wednesday": "09:00-19:00",
        "thursday": "09:00-19:00",
        "friday": "09:00-19:00",
        "saturday": "09:00-15:00",
        "sunday": "Fechado",
    },
    {
        "monday": "Atendimento 24 horas",
        "tuesday": "Atendimento 24 horas",
        "wednesday": "Atendimento 24 horas",
        "thursday": "Atendimento 24 horas",
        "friday": "Atendimento 24 horas",
        "saturday": "Atendimento 24 horas",
        "sunday": "Atendimento 24 horas",
    },
]


def _slugify(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text or "")
    ascii_text = norm.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "geralead"


def _mock_phone(rng: random.Random) -> str:
    ddd = rng.randint(11, 99)
    suffix_a = rng.randint(1000, 9999)
    suffix_b = rng.randint(1000, 9999)
    return f"55{ddd}9{suffix_a}{suffix_b}"


def build_mock_items(sector: str, address: str, max_results: int) -> list[dict]:
    max_results = _clamp(max_results, 1, 1000)

    address_parts = [p.strip() for p in address.split(",") if p.strip()]
    city = address_parts[0] if address_parts else "Cidade Exemplo"
    state = address_parts[1] if len(address_parts) > 1 else "SE"

    sector_slug = _slugify(sector)
    city_slug = _slugify(city)
    seed_input = f"{sector_slug}|{city_slug}|{max_results}"
    rng_seed = sum((idx + 1) * ord(ch) for idx, ch in enumerate(seed_input)) & 0xFFFFFFFF
    rng = random.Random(rng_seed)

    mock_items: list[dict] = []
    for idx in range(1, max_results + 1):
        prefix = rng.choice(MOCK_NAME_PREFIXES)
        suffix = rng.choice(MOCK_NAME_SUFFIXES)
        street = rng.choice(MOCK_STREETS)
        neighborhood = rng.choice(MOCK_NEIGHBORHOODS)
        number = rng.randint(10, 999)

        # Domínios .test são reservados e seguros para dados fictícios.
        domain = f"{sector_slug}-{city_slug}-{idx}.example.test"
        place_name = f"{sector.title()} {prefix} {suffix} {idx}"
        website = f"https://{domain}"
        maps_url = f"https://maps.example.test/{city_slug}/{sector_slug}/{idx}"

        mock_items.append(
            {
                "placeName": place_name,
                "address": f"Rua {street}, {number} - {neighborhood}, {city} - {state}",
                "phone": _mock_phone(rng),
                "rating": round(rng.uniform(3.5, 5.0), 1),
                "reviewsCount": rng.randint(8, 800),
                "website": website,
                "url": maps_url,
                "placeId": f"mock-{city_slug}-{sector_slug}-{idx}",
                "openingHours": rng.choice(MOCK_HOURS_TEMPLATES),
            }
        )

    return mock_items


# -------------------- apify --------------------

async def run_apify_search(run_input: dict) -> Dict[str, Any]:
    if not APIFY_ACTOR_ID:
        raise RuntimeError("APIFY_ACTOR_ID não configurado.")
    client = make_client()
    run = await asyncio.to_thread(client.actor(APIFY_ACTOR_ID).call, run_input=run_input)
    if not run:
        raise RuntimeError("Apify não retornou resultado do run.")
    return run

async def fetch_items_from_dataset(dataset_id: str, limit: int = 1000, offset: int = 0) -> list[dict]:
    limit = _clamp(limit, 1, 1000)
    client = make_client()
    dataset_client = client.dataset(dataset_id)

    def _load():
        page = dataset_client.list_items(limit=limit, offset=offset)
        return getattr(page, "items", [])

    return await asyncio.to_thread(_load)

# -------------------- persistência --------------------

async def bulk_insert_results(
    session: AsyncSession,
    items: Iterable[Dict[str, Any]],
    *,
    search_id: int,
) -> Tuple[int, int]:
    """
    Insere em massa LeadResult. Retorna (inseridos, ignorados_por_conflito).
    UNIQUE recomendada: (search_id, source_id). Se não houver source_id, caia para (search_id, url).
    """
    rows = [map_apify_item_to_result_row(it, search_id) for it in items]

    valid = [r for r in rows if r.get("url") or r.get("source_id")]
    if not valid:
        return (0, 0)

    # detecta coluna disponível para conflito
    if "source_id" in LeadResult.__table__.c:
        conflict_cols = [LeadResult.search_id, LeadResult.source_id]
    else:
        conflict_cols = [LeadResult.search_id, LeadResult.url]

    stmt = pg_insert(LeadResult).values(valid).on_conflict_do_nothing(index_elements=conflict_cols)
    result = await session.execute(stmt)
    inserted = result.rowcount or 0
    ignored = max(len(valid) - inserted, 0)
    return inserted, ignored

async def start_and_persist_search(
    session: AsyncSession,
    *,
    user_id: int,
    sector: str,
    address: str,
    radius_km: float,
    max_results: int = 100,
) -> Dict[str, Any]:
    """
    1) Geocodifica
    2) Cria LeadSearch (cabeçalho) e COMMIT (aparece no histórico)
    3) Executa Apify
    4) Insere LeadResult em massa
    5) Atualiza contadores do LeadSearch
    """
    max_results = _clamp(max_results, 1, 1000)
    lat, lng = await geocode(address)

    # 1. Cria o cabeçalho da busca e confirma de imediato
    search = LeadSearch(
        user_id=user_id,
        query=sector,  # se seu modelo usa 'term', troque aqui e nos templates
        params={"address": address, "radius_km": radius_km, "max_results": max_results, "lat": lat, "lng": lng},
        started_at=datetime.now(timezone.utc),
    )
    session.add(search)
    await session.flush()
    await session.commit()  # garante search.id e já aparece no /historico

    # 2. Executa o ator e coleta itens
    run_input = build_run_input(sector, lat, lng, radius_km, max_results)
    run = await run_apify_search(run_input)
    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        raise RuntimeError("Run executado, mas sem 'defaultDatasetId'.")

    items = await fetch_items_from_dataset(dataset_id, limit=max_results, offset=0)

    # 3. Insere resultados
    inserted, ignored = await bulk_insert_results(session, items, search_id=search.id)

    # 4. Atualiza o cabeçalho e confirma
    search.finished_at = datetime.now(timezone.utc)
    search.results_count = inserted  # ou use len(items) se quiser total coletado
    await session.commit()

    # app/services/lead_services.py
    return {
        "search_id": search.id,
        "dataset_id": dataset_id,
        "total_coletado": len(items),
        "inseridos": inserted,
        "ignorados_por_conflito": ignored,
    }


async def start_and_persist_mock_search(
    session: AsyncSession,
    *,
    user_id: int,
    sector: str,
    address: str,
    radius_km: float,
    max_results: int = 100,
) -> Dict[str, Any]:
    """
    Gera e persiste dados 100% fictícios, sem consumir APIs externas.
    """
    max_results = _clamp(max_results, 1, 1000)

    search = LeadSearch(
        user_id=user_id,
        query=sector,
        params={
            "address": address,
            "radius_km": radius_km,
            "max_results": max_results,
            "mode": "mock",
        },
        started_at=datetime.now(timezone.utc),
    )
    session.add(search)
    await session.flush()
    await session.commit()

    items = build_mock_items(sector=sector, address=address, max_results=max_results)
    inserted, ignored = await bulk_insert_results(session, items, search_id=search.id)

    search.finished_at = datetime.now(timezone.utc)
    search.results_count = inserted
    await session.commit()

    return {
        "search_id": search.id,
        "dataset_id": f"mock-{search.id}",
        "total_coletado": len(items),
        "inseridos": inserted,
        "ignorados_por_conflito": ignored,
    }


# -------------------- consultas p/ UI --------------------

async def list_searches(
    session: AsyncSession,
    *,
    user_id: int | None,
    is_admin: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[LeadSearch]:
    """
    Lista histórico de buscas. Admin vê todas; usuário comum só as dele.
    """
    # usar ID é mais resiliente do que started_at (que pode vir nulo)
    stmt = select(LeadSearch).order_by(LeadSearch.id.desc()).limit(limit).offset(offset)
    if not is_admin:
        stmt = stmt.where(LeadSearch.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_search_by_id(session: AsyncSession, *, search_id: int) -> LeadSearch | None:
    return await session.get(LeadSearch, search_id)

async def list_results_by_search(
    session: AsyncSession,
    *,
    search_id: int,
    limit: int = 500,
    offset: int = 0,
) -> Sequence[LeadResult]:
    stmt = (
        select(LeadResult)
        .where(LeadResult.search_id == search_id)
        .order_by(LeadResult.id.asc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

# (Opcional) versão que já aplica autorização na query
async def list_results_by_search_for_user(
    session: AsyncSession,
    *,
    search_id: int,
    user_id: int,
    is_admin: bool,
    limit: int = 500,
    offset: int = 0,
) -> Sequence[LeadResult]:
    stmt = (
        select(LeadResult)
        .join(LeadSearch, LeadResult.search_id == LeadSearch.id)
        .where(LeadResult.search_id == search_id)
        .order_by(LeadResult.id.asc())
        .limit(limit)
        .offset(offset)
    )
    if not is_admin:
        stmt = stmt.where(LeadSearch.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()
