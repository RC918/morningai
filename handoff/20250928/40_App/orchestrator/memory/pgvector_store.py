import os
from supabase import create_client
from openai import OpenAI

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
TABLE = os.getenv("MEMORY_TABLE", "memory")

def get_client():
    """Get Supabase client, creating it only when needed"""
    try:
        if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
            return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        else:
            print("[Memory] Supabase credentials not available")
            return None
    except Exception as e:
        print(f"[Memory] Failed to create Supabase client: {e}")
        return None

def embed(text:str):
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        cl = OpenAI(api_key=api_key)
        emb = cl.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding
        return emb
    except Exception as e:
        print(f"[Memory] Failed to get embedding: {e}")
        return None

def save_text(key:str, text:str):
    try:
        client = get_client()
        if client is None:
            print("[Memory] Supabase client not available")
            return
        vec = embed(text) or []
        client.table(TABLE).insert({"key": key, "text": text, "embedding": vec}).execute()
    except Exception as e:
        print(f"[Memory] Failed to save text: {e}")

def recall_top(keywords:str, limit:int=5):
    # Simplified: just return recent items. For real vector search, set up a SQL function.
    try:
        client = get_client()
        if client is None:
            print("[Memory] Supabase client not available")
            return []
        res = client.table(TABLE).select("*").order("id", desc=True).limit(limit).execute()
        return res.data or []
    except Exception as e:
        print(f"[Memory] Failed to recall memories: {e}")
        return []
