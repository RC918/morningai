import os
from supabase import create_client
from openai import OpenAI

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
TABLE = os.getenv("MEMORY_TABLE", "memory")

client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def embed(text:str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    cl = OpenAI(api_key=api_key)
    emb = cl.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding
    return emb

def save_text(key:str, text:str):
    if client is None:
        return
    vec = embed(text) or []
    client.table(TABLE).insert({"key": key, "text": text, "embedding": vec}).execute()

def recall_top(keywords:str, limit:int=5):
    # Simplified: just return recent items. For real vector search, set up a SQL function.
    if client is None:
        return []
    res = client.table(TABLE).select("*").order("id", desc=True).limit(limit).execute()
    return res.data or []
