# GeraLead API

Backend em FastAPI para autenticação de usuários, geração de leads e histórico de buscas.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy Async
- PostgreSQL
- Alembic
- JWT

## Modo Mock (padrão)

O endpoint de busca já está configurado para gerar dados fictícios por padrão (`use_mock=true`).
Isso permite testar o sistema sem depender de Apify/Google.

## Requisitos

1. Criar e ativar ambiente virtual.
2. Instalar dependências:

```bash
python -m pip install -r requirements.txt
```

3. Criar o `.env` com base em `.env.example`.

## Executar API

```bash
python -m uvicorn app.main:app --reload
```

Documentação:

- `http://127.0.0.1:8000/docs`

## Banco de dados

Aplicar migrations:

```bash
alembic upgrade head
```

## Fluxo principal

1. Registrar usuário em `/registrar` (UI) ou `/docs`.
2. Fazer login em `/login`.
3. Iniciar busca em `POST /search/start`.
4. Consultar resultados em `GET /api/searches/{search_id}/results`.
5. Exportar em `/export/{search_id}?format=csv|xlsx|pdf`.

## Exemplo de busca mockada

Request:

```json
{
  "sector": "Restaurantes",
  "address": "Joao Pessoa, PB",
  "radius_km": 5,
  "max_results": 10,
  "use_mock": true
}
```

Response (resumo):

```json
{
  "search_id": 12,
  "dataset_id": "mock-12",
  "total_coletado": 10,
  "inseridos": 10,
  "ignorados_por_conflito": 0
}
```

## Busca real (Apify + Google)

Para usar busca real, preencha no `.env`:

- `APIFY_TOKEN`
- `APIFY_ACTOR_ID`
- `GOOGLE_API_KEY`

E envie no payload:

```json
{
  "use_mock": false
}
```

## Segurança e configuração

- Não versione `.env` com segredos.
- Use `.env.example` como modelo.
- Gere `SECRET_KEY` forte para produção.
