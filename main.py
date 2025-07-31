from fastapi import FastAPI
from fastapi.responses import JSONResponse

import pandas as pd
import fitz  # PyMuPDF
import os

from supabase import create_client
import weaviate
from weaviate.auth import AuthClientPassword
# import uuid for item in all_items:
#             path = item.get("name")
#             if path and path.startswith("customer-documents/"):
#                 filename = path.split("/")[-1]
#                 file_url = (
#                     f"https://{SUPABASE_URL.split('//')[-1]}/storage/v1/object/public/"
#                     f"{SUPABASE_BUCKET_NAME}/{path}"
#                 )
#                 file_urls.append(file_url)

#         return {"files": file_urls}
import requests

app = FastAPI()

# Load env vars (Render auto-loads them from settings)
SUPABASE_URL = "https://rrszjwwsddrtkltomjkh.supabase.co"
# os.getenv("SUPABASE_URL")
SUPABASE_KEY = "sb_publishable_YaJyiHBaNtOlC30oog6lDg_D7tiMRmt"
# os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET_NAME = "customer-documents"
# os.getenv("SUPABASE_BUCKET_NAME")
WEAVIATE_URL = "https://0d9dwglxtsqxkapzbxhpra.c0.asia-southeast1.gcp.weaviate.cloud"
# os.getenv("WEAVIATE_URL")
WEAVIATE_USERNAME = "vibhor.goyal@woodenstreet.com"
WEAVIATE_PASSWORD = "Vibhor@7890"
GROQ_API_KEY = "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"
# os.getenv("GROQ_API_KEY")

# Setup Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
@app.get("/list-files")
def list_files():
    try:
        all_items = supabase.storage.from_(customer-documents).list("documents", {"limit": 1000, "offset": 0})

        print("ALL items in bucket:", all_items)

        file_urls = []

        # for item in all_items:
        #     path = item.get("name")
        #     if path and path.startswith("customer-documents/"):
        #         filename = path.split("/")[-1]
        #         file_url = (
        #             f"https://{SUPABASE_URL.split('//')[-1]}/storage/v1/object/public/"
        #             f"{SUPABASE_BUCKET_NAME}/{path}"
        #         )
        #         file_urls.append(file_url)

        # return {"files": file_urls}
        return (all_items)
    except Exception as e:
        return {"error": str(e)}


        
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
