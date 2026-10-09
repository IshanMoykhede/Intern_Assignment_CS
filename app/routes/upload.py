
import os
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.session import ChatSession
from app.models.document import Document
from app.services.data_ingestion import ingest_document

router = APIRouter()

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, and TXT files are supported"
        )

    session = ChatSession()
    db.add(session)
    db.commit()
    db.refresh(session)

    document_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{document_id}{extension}")

    try:
        # 1. Save uploaded file
        with open(file_path, "wb") as output:
            while chunk := file.file.read(1024 * 1024):
                output.write(chunk)

        # 2. Save document metadata in SQLite
        document = Document(
            id=document_id,
            session_id=session.id,
            filename=file.filename,
            file_path=file_path
        )
        db.add(document)
        db.commit()

        # 3. Extract, chunk, embed, and store in ChromaDB
        result = ingest_document(
            file_path=file_path,
            session_id=session.id,
            document_id=document_id,
            filename=file.filename
        )

        # 4. Return ingestion result
        return {
            "success": True,
            "session_id": session.id,
            "document_id": document_id,
            "filename": file.filename,
            "chunks_stored": result["chunks_stored"]
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(error)}"
        )

    finally:
        file.file.close()
