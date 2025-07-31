from fastapi import FastAPI
from fastapi.responses import JSONResponse
import pandas as pd
import fitz  # PyMuPDF
import os
import requests

from supabase import create_client
import weaviate
from weaviate.auth import AuthClientPassword

app = FastAPI()

# Load config
SUPABASE_URL = "https://rrszjwwsddrtkltomjkh.supabase.co"
SUPABASE_KEY = "sb_publishable_YaJyiHBaNtOlC30oog6lDg_D7tiMRmt"
SUPABASE_BUCKET_NAME = "documents"
WEAVIATE_URL = "https://0d9dwglxtsqxkapzbxhpra.c0.asia-southeast1.gcp.weaviate.cloud"
WEAVIATE_USERNAME = "vibhor.goyal@woodenstreet.com"
WEAVIATE_PASSWORD = "Vibhor@7890"
GROQ_API_KEY = "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"

# Setup Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Setup Weaviate client
client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=AuthClientPassword(
        username=WEAVIATE_USERNAME,
        password=WEAVIATE_PASSWORD
    )
)

@app.get("/")
def read_root():
    return {"message": "RAG Backend is Live 🎉"}


@app.get("/list-files")
def list_files():
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }

        # List files in root of bucket
        url_root = f"{SUPABASE_URL}/storage/v1/object/list/{SUPABASE_BUCKET_NAME}?limit=100"
        root_resp = requests.get(url_root, headers=headers)
        root_files = root_resp.json()

        # List files inside 'documents/' folder
        # url_folder = f"{SUPABASE_URL}/storage/v1/object/list/{SUPABASE_BUCKET_NAME}?prefix=documents/&limit=100"
        # folder_resp = requests.get(url_folder, headers=headers)
        # folder_files = folder_resp.json()

        # Combine all paths into full public URLs
        file_urls = []

        for item in root_files:
            name = item.get("name")
            file_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET_NAME}/{name}"
            file_urls.append(file_url)

        # for item in folder_files:
        #     name = item.get("name")
        #     file_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET_NAME}/{name}"
        #     file_urls.append(file_url)

        return {"files": file_urls}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



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
        return {"content": text[:500]}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
