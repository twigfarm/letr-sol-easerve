from langchain_pinecone import PineconeVectorStore
from my_agent.utils.embedding import embedding

breeds_database_index = "breeds"
breeds_database = PineconeVectorStore(
    index_name=breeds_database_index,
    embedding=embedding
)
