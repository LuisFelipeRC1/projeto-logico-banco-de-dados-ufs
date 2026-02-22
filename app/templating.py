from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory='app/templates')

def compress_hours(rows: list[dict] | None) -> list[str]:
    if not rows:
        return []
    # se todos são 24h
    if all((r.get("hours","").lower().startswith("atendimento 24") or r.get("hours","").lower().startswith("24")) for r in rows):
        return ["24h (todos os dias)"]

    # agrupa por horas iguais e consecutivas
    order = {d:i for i,d in enumerate([
        "segunda-feira","terça-feira","quarta-feira","quinta-feira","sexta-feira","sábado","domingo"
    ])}
    rows = sorted(rows, key=lambda r: order.get(r["day"], 99))

    buckets = []
    cur = {"start": rows[0]["day"], "end": rows[0]["day"], "hours": rows[0]["hours"]}
    for r in rows[1:]:
        if r["hours"] == cur["hours"] and order.get(r["day"], 99) == order.get(cur["end"],99) + 1:
            cur["end"] = r["day"]
        else:
            buckets.append(cur)
            cur = {"start": r["day"], "end": r["day"], "hours": r["hours"]}
    buckets.append(cur)

    def short(d: str) -> str:
        return {
            "segunda-feira":"Seg","terça-feira":"Ter","quarta-feira":"Qua",
            "quinta-feira":"Qui","sexta-feira":"Sex","sábado":"Sáb","domingo":"Dom"
        }.get(d, d)

    out = []
    for b in buckets:
        label = short(b["start"]) if b["start"] == b["end"] else f"{short(b['start'])}–{short(b['end'])}"
        out.append(f"{label}: {b['hours']}")
    return out

# no setup do Jinja2, registre:
templates.env.filters["compress_hours"] = compress_hours
