import os
from langchain_upstage import UpstageEmbeddings
from dotenv import load_dotenv

load_dotenv()
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
embedding = UpstageEmbeddings(
    api_key=UPSTAGE_API_KEY,
    model="embedding-query"
)
