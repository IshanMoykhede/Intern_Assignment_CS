
# pyrefly: ignore [missing-import]
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

CHROMA_DIR = "data/chroma"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vector_store = Chroma(
    collection_name="document_chunks",
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings
)


def retrieve_chunks(query: str, session_id: str, k: int = 5):
    results = vector_store.similarity_search(
        query,
        k=k,
        filter={"session_id": session_id}
    )

    return [
        {
            "content": doc.page_content,
            "filename": doc.metadata["filename"],
            "page": doc.metadata["page"],
            "chunk_index": doc.metadata["chunk_index"]
        }
        for doc in results
    ]
