import weaviate

client = weaviate.Client(
    url="https://0d9dwglxtsqxkapzbxhpra.c0.asia-southeast1.gcp.weaviate.cloud"
)

def get_weaviate_client():
    return client

