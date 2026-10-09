
import os
from pypdf import PdfReader
from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
# pyrefly: ignore [missing-import]
from langchain_community.embeddings import HuggingFaceEmbeddings
# pyrefly: ignore [missing-import]
from langchain_chroma import Chroma


# Directories
CHROMA_DIR = "data/chroma"
os.makedirs(CHROMA_DIR, exist_ok=True)

# Embedding model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Text chunker
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)


def extract_text(file_path: str):
    """Extract text and page numbers from PDF, DOCX, or TXT files."""
    extension = os.path.splitext(file_path)[1].lower()
    pages = []

    if extension == ".pdf":
        reader = PdfReader(file_path)
        for page_number, page in enumerate(reader.pages, start=1):
            pages.append({
                "text": page.extract_text() or "",
                "page": page_number
            })

    elif extension == ".docx":
        doc = DocxDocument(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)
        pages.append({"text": text, "page": 1})

    elif extension == ".txt":
        with open(file_path, "r", encoding="utf-8") as file:
            pages.append({"text": file.read(), "page": 1})

    else:
        raise ValueError("Only PDF, DOCX, and TXT files are supported.")

    return pages


def ingest_document(
    file_path: str,
    session_id: str,
    document_id: str,
    filename: str
):
    """Extract, chunk, embed, and store document content."""
    pages = extract_text(file_path)

    chunks = []
    metadatas = []

    for page_data in pages:
        text_chunks = text_splitter.split_text(page_data["text"])

        for chunk_index, chunk in enumerate(text_chunks):
            chunks.append(chunk)
            metadatas.append({
                "session_id": session_id,
                "document_id": document_id,
                "filename": filename,
                "page": page_data["page"],
                "chunk_index": chunk_index
            })

    if not chunks:
        raise ValueError("No readable text found in the document.")

    vector_store = Chroma(
        collection_name="document_chunks",
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )

    vector_store.add_texts(
        texts=chunks,
        metadatas=metadatas
    )

    return {"chunks_stored": len(chunks)}
