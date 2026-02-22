from __future__ import annotations
import io
import csv
import os
from typing import List

# Arquivos
import openpyxl
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse
from reportlab.lib.units import inch

# Templates
from app.templating import compress_hours, templates

# Auth/security
from app.auth.security import (
    get_password_hash,
    authenticate_user,
    issue_access_token_for_user,
    decode_token_to_data,
)

# DB / Models / Schemas / Services
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserCreate
# ⛔️ REMOVIDO: LeadOut do modelo antigo
# from app.schemas.lead import LeadOut
from app.schemas.lead import SearchOut, ResultOut  # (se você criou estes; senão pode retirar o response_model)
from app.services.lead_services import (
    list_searches,
    list_results_by_search,
    get_search_by_id,
)

router = APIRouter(tags=["auth"])


# --------- Utils ---------

async def get_current_user_from_cookie(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User:
    token = request.cookies.get("Authorization")
    credentials_exception = HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        detail="Not authenticated",
        headers={"Location": "/login"},
    )
    if not token:
        raise credentials_exception

    try:
        scheme, _, param = token.partition(" ")
        if scheme.lower() != "bearer":
            raise credentials_exception
        token_data = await decode_token_to_data(param)
        if token_data.user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = await session.get(User, token_data.user_id)
    if user is None:
        raise credentials_exception
    return user


# --------- Páginas e Auth ---------

@router.get("/registrar", response_class=HTMLResponse, include_in_schema=False)
async def registrar_get(request: Request):
    return templates.TemplateResponse("registrar.html", {"request": request, "msg": None})


@router.post("/registrar", status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    form: UserCreate = Depends(UserCreate.as_form),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(select(User).where(User.email == form.email))
    if existing.scalars().first():
        return templates.TemplateResponse(
            "registrar.html",
            {"request": request, "msg": "Este e-mail já está cadastrado."},
            status_code=409
        )
    user = User(
        nome=form.nome,
        email=form.email,
        cpf=form.cpf,
        phone=form.phone,
        hashed_password=get_password_hash(form.password),
        role="user",
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return templates.TemplateResponse(
            "registrar.html",
            {"request": request, "msg": "Erro: CPF ou outro dado já cadastrado."},
            status_code=409
        )
    return RedirectResponse(url="/login?msg=Conta+criada!+Faça+login.", status_code=303)


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_get(request: Request):
    msg = request.query_params.get("msg")
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})


@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(session, email=form_data.username, password=form_data.password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "msg": "E-mail ou senha inválidos."},
            status_code=400
        )
    access_token = await issue_access_token_for_user(user)
    resp = RedirectResponse(url="/home", status_code=303)
    resp.set_cookie(
        key="Authorization",
        value=f"Bearer {access_token}",
        httponly=True, samesite="lax", secure=False, max_age=3600, path="/",
    )
    return resp


@router.get("/login-success", response_class=HTMLResponse, include_in_schema=False)
async def login_success(request: Request):
    return templates.TemplateResponse("login_success.html", {"request": request})


@router.get("/home", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    maps_key = os.getenv("MAPS_JAVASCRIPT_SECRETKEY") or os.getenv("GOOGLE_API_KEY") or ""
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "current_user": current_user, "google_maps_api_key": maps_key},
    )


@router.get("/historico", response_class=HTMLResponse, include_in_schema=False)
async def historico_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session),
):
    searches = await list_searches(
        session,
        user_id=current_user.id,
        is_admin=(current_user.role == "admin"),
        limit=100,
        offset=0,
    )
    return templates.TemplateResponse(
        "historico.html",
        {"request": request, "current_user": current_user, "searches": searches}
    )


@router.get("/historico/{search_id}", response_class=HTMLResponse, include_in_schema=False)
async def historico_detalhe_page(
    search_id: int,
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session),
):
    search = await get_search_by_id(session, search_id=search_id)
    if not search:
        return RedirectResponse(url="/historico?msg=Busca+não+encontrada.", status_code=303)

    # usuário comum só acessa o próprio; admin acessa tudo
    if current_user.role != "admin" and search.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    results = await list_results_by_search(session, search_id=search_id, limit=500, offset=0)
    return templates.TemplateResponse(
        "historico_detalhe.html",
        {"request": request, "current_user": current_user, "search": search, "results": results}
    )


@router.get("/logout", response_class=RedirectResponse, include_in_schema=False)
async def logout(request: Request):
    response = RedirectResponse(url="/login?msg=Logout+realizado+com+sucesso.", status_code=303)
    response.delete_cookie("Authorization")
    return response


# --------- APIs JSON (novas) ---------

@router.get("/api/searches", response_model=List[SearchOut])
async def api_list_searches(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session),
):
    searches = await list_searches(
        session,
        user_id=current_user.id,
        is_admin=(current_user.role == "admin"),
        limit=limit,
        offset=offset,
    )
    return searches


@router.get("/api/searches/{search_id}/results", response_model=List[ResultOut])
async def api_list_results_by_search(
    search_id: int,
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session),
):
    # autorização: só dono ou admin
    search = await get_search_by_id(session, search_id=search_id)
    if not search:
        raise HTTPException(status_code=404, detail="Busca não encontrada.")
    if current_user.role != "admin" and search.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    results = await list_results_by_search(session, search_id=search_id, limit=limit, offset=offset)
    return results


# --------- Exportação ---------

@router.get("/export/{search_id}", include_in_schema=False)
async def export_leads(
    search_id: int,
    format: str,
    current_user: User = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session),
):
    # Verifica permissão
    search = await get_search_by_id(session, search_id=search_id)
    if not search or (current_user.role != "admin" and search.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="Busca não encontrada ou sem permissão.")

    leads = await list_results_by_search(session, search_id=search_id, limit=5000)
    if not leads:
        raise HTTPException(status_code=404, detail="Nenhum lead nesta busca para exportar.")

    # Cabeçalho e dados com os CAMPOS NOVOS do LeadResult
    headers = ["Nome", "Endereço", "Telefone", "Avaliação", "Quantidade de Avaliações", "Website/Rede Social", "Horário de Funcionamento","URL no Mapa"]
    data = [
        [
            (l.place_name or ""),
            (l.address or ""),
            (l.phone or ""),
            ("" if l.rating is None else str(l.rating)),
            ("" if l.reviews_count is None else str(l.reviews_count)),
            (l.website or ""),
            "\n".join(compress_hours(getattr(l, "opening_hours", None))) if getattr(l, "opening_hours", None) else "",
            (l.url or ""),
        ]
        for l in leads
    ]

    if format == "csv":
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(data)
        stream.seek(0)
        return StreamingResponse(
            iter([stream.read()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=busca_{search_id}_leads.csv"},
        )

    elif format == "xlsx":
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = f"Busca {search_id}"
        sheet.append(headers)
        for row in data:
            sheet.append(row)
        stream = io.BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=busca_{search_id}_leads.xlsx"},
        )

    elif format == "pdf":
        stream = io.BytesIO()
        doc = SimpleDocTemplate(
            stream,
            pagesize=landscape(A4),
            leftMargin=18, rightMargin=18, topMargin=22, bottomMargin=22
        )

        # estilos mínimos (cabeçalho e células com quebra de linha)
        styles = getSampleStyleSheet()
        head = ParagraphStyle('head', parent=styles['Normal'], fontName='Helvetica-Bold',
                            fontSize=9, textColor=colors.whitesmoke, alignment=1)
        cell = ParagraphStyle('cell', parent=styles['Normal'], fontName='Helvetica',
                            fontSize=8, leading=10)
        style_cell = ParagraphStyle('cell_hours', fontName='Helvetica', fontSize=8, leading=10)


        # cabeçalho + linhas (usa objetos "leads" do detalhe da busca)
        table_data = [[
            Paragraph("Nome", head),
            Paragraph("Endereço", head),
            Paragraph("Telefone", head),
            Paragraph("Avaliação", head),
            Paragraph("Quantidade de Avaliações", head),
            Paragraph("Website/Rede Social", head),
            Paragraph("Horário de Funcionamento", head),
            Paragraph("URL", head),
        ]]

        for l in leads:
            hor = "\n".join(compress_hours(getattr(l, "opening_hours", None))) if getattr(l, "opening_hours", None) else "—"
            table_data.append([
                Paragraph(l.place_name or "—", cell),
                Paragraph(l.address or "—", cell),
                Paragraph(l.phone or "—", cell),
                Paragraph(str(l.rating if l.rating is not None else "—"), cell),
                Paragraph(str(l.reviews_count or 0), cell),
                Paragraph(l.website or "—", cell),
                Paragraph(hor, style_cell),
                Paragraph(l.url or "—", cell),
            ])

        table = Table(
            table_data,
            colWidths=[1.6*inch, 2.1*inch, 1.1*inch, 0.7*inch, 0.9*inch, 1.2*inch, 1.5*inch, 1.9*inch],
            repeatRows=1
        )
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#00AEEF')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.25, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (3,1), (4,-1), 'CENTER'),  # números centralizados
        ]))

        doc.build([table])
        stream.seek(0)
        return StreamingResponse(
            stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=busca_{search_id}_leads.pdf"},
        )


    else:       
        raise HTTPException(status_code=400, detail="Formato de exportação inválido.")
