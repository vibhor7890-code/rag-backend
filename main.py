from fastapi import FastAPI
from fastapi.responses import JSONResponse

import pandas as pd
import fitz  # PyMuPDF
import os

from supabase import create_client
from weaviate.util import get_valid_uuid
import weaviate
import uuid
import requests

app = FastAPI()

# Load env vars (Render auto-loads them from settings)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Setup Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Setup Weaviate client
client = weaviate.Client(
    url=WEAVIATE_URL,
    additional_headers={
        "X-OpenAI-Api-Key": "",  # Not required for public instance
    }
)


@app.get("/")
def read_root():
    return {"message": "RAG Backend is Live 🎉"}


@app.get("/test/supabase")
def test_supabase():
    try:
        result = supabase.storage.from_(SUPABASE_BUCKET_NAME).list()
        return {"status": "success", "files": result}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/test/weaviate")
def test_weaviate():
    try:
        if client.is_ready():
            return {"status": "Weaviate connected ✅"}
        else:
            return JSONResponse(content={"error": "Weaviate not ready"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/test/pandas")
def test_pandas():
    try:
        df = pd.DataFrame({
            "order_id": [101, 102],
            "customer": ["Alice", "Bob"]
        })
        return df.to_dict()
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/test/pdf")
def test_pdf():
    try:
        file_path = "sample.pdf"
        if not os.path.exists(file_path):
            return {"message": "sample.pdf not found. Please upload it."}

        with fitz.open(file_path) as pdf:
            text = ""
            for page in pdf:
                text += page.get_text()
        return {"content": text[:500]}  # return only 1st 500 characters
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
