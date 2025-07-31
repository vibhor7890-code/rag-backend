from fastapi import FastAPI
from fastapi.responses import JSONResponse
import pandas as pd
import fitz  # PyMuPDF
import os
import requests

from supabase import create_client
import weaviate
from weaviate.auth import AuthClientPassword

from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

import tempfile

app = FastAPI()

# Load config
SUPABASE_URL = "https://rrszjwwsddrtkltomjkh.supabase.co"
SUPABASE_KEY = "sb_publishable_YaJyiHBaNtOlC30oog6lDg_D7tiMRmt"
SUPABASE_BUCKET_NAME = "customer-documents"
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
    # ✅ Use direct public URLs manually
    file_urls = [
        "https://rrszjwwsddrtkltomjkh.supabase.co/storage/v1/object/public/customer-documents//Defective_Product_Policy.pdf",
        "https://rrszjwwsddrtkltomjkh.supabase.co/storage/v1/object/public/customer-documents//Different_Product_Received_Policy.pdf",
        "https://rrszjwwsddrtkltomjkh.supabase.co/storage/v1/object/public/customer-documents//Installation_List.csv",
        "https://rrszjwwsddrtkltomjkh.supabase.co/storage/v1/object/public/customer-documents//Order_List.csv",
        "https://rrszjwwsddrtkltomjkh.supabase.co/storage/v1/object/public/customer-documents//Warranty_Claim_Policy.pdf"
    ]
    return {"files": file_urls}

embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
@app.get("/ingest-docs")
def ingest_documents():
    try:
        # Step 1: List files
        result = supabase.storage.from_(SUPABASE_BUCKET_NAME).list("", {"limit": 1000})
        urls = [
            f"https://{SUPABASE_URL.split('//')[-1]}/storage/v1/object/public/{SUPABASE_BUCKET_NAME}/{item['name']}"
            for item in result if item["name"].endswith((".pdf", ".csv"))
        ]
        
        if not urls:
            return {"message": "No PDF or CSV files found."}

        for url in urls:
            response = requests.get(url)
            if response.status_code != 200:
                continue

            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(response.content)
                file_path = tmp_file.name

            # Extract content
            if url.endswith(".pdf"):
                with fitz.open(file_path) as pdf:
                    text = ""
                    for page in pdf:
                        text += page.get_text()
            elif url.endswith(".csv"):
                df = pd.read_csv(file_path)
                text = df.to_string()
            else:
                continue

            # Chunk text
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_text(text)

            # Embed and upload to Weaviate
            for i, chunk in enumerate(chunks):
                embedding = embed_model.encode(chunk).tolist()
                client.data_object.create(
                    {
                        "text": chunk,
                        "source": url
                    },
                    class_name="Document",
                    vector=embedding
                )

        return {"status": "success", "message": "Documents processed and embedded."}

    except Exception as e:
        return {"error": str(e)}

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
