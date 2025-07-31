from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "RAG backend is running!"}

# Run the app when deployed on Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)


import weaviate
import pandas as pd
import fitz  # PyMuPDF
import requests
from supabase import create_client
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# Setup Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Setup Weaviate
client = weaviate.Client(
    url=os.getenv("WEAVIATE_URL"),
    additional_headers={"X-OpenAI-Api-Key": ""}  # leave empty if not needed
)

# Embedding model
embedder = SentenceTransformer("BAAI/bge-base-en-v1.5")
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

def read_pdf_text(url):
    resp = requests.get(url)
    doc = fitz.open(stream=resp.content, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)

def index_document_in_weaviate(content, metadata):
    texts = splitter.split_text(content)
    vectors = embedder.encode(texts).tolist()
    for text, vector in zip(texts, vectors):
        client.data_object.create(
            {"text": text, **metadata},
            class_name="CustomerDocs",
            vector=vector
        )

@app.get("/index-all")
def index_all_files():
    # Create class in Weaviate (if not already)
    if not client.schema.contains({"class": "CustomerDocs"}):
        client.schema.create_class({
            "class": "CustomerDocs",
            "vectorizer": "none",
            "properties": [{"name": "text", "dataType": ["text"]}]
        })

    bucket = os.getenv("SUPABASE_BUCKET_NAME")

    files = supabase.storage.from_(bucket).list()
    for file in files:
        file_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{bucket}/{file['name']}"
        if file["name"].endswith(".csv"):
            df = pd.read_csv(file_url)
            index_document_in_weaviate(df.to_csv(index=False), {"filename": file["name"]})
        elif file["name"].endswith(".pdf"):
            pdf_text = read_pdf_text(file_url)
            index_document_in_weaviate(pdf_text, {"filename": file["name"]})
    return {"status": "Files indexed to Weaviate"}
