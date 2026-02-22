import os
from dotenv import load_dotenv
from apify_client import ApifyClient 

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
APIFY_ACTOR_ID = os.getenv("APIFY_ACTOR_ID")  

def make_client() -> ApifyClient:
    if not APIFY_TOKEN:
        raise RuntimeError("APIFY_TOKEN não configurado no .env")
    return ApifyClient(APIFY_TOKEN)
