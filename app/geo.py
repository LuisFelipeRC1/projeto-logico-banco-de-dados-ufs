import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def _get_google_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY não configurado no .env")
    return api_key

async def geocode(address: str) -> tuple[float, float]:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            GEOCODE_URL,
            params={"address": address, "key": _get_google_api_key()},
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "OK" or not data.get("results"):
            raise ValueError(f"Endereço não encontrado: {address}")
        loc = data["results"][0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])
