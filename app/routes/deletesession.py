
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.session import ChatSession
from app.models.document import Document
from app.models.chat import Chat
from app.services.data_retrieval import vector_store

router = APIRouter()


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    try:
        # 1. Find the session
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )

        # 2. Get documents belonging to the session
        documents = db.query(Document).filter(
            Document.session_id == session_id
        ).all()

        # 3. Delete document chunks from ChromaDB
        vector_store.delete(
            where={"session_id": session_id}
        )

        # 4. Delete uploaded files
        for document in documents:
            if os.path.isfile(document.file_path):
                os.remove(document.file_path)

        # 5. Delete chat history
        db.query(Chat).filter(
            Chat.session_id == session_id
        ).delete(synchronize_session=False)

        # 6. Delete document records
        db.query(Document).filter(
            Document.session_id == session_id
        ).delete(synchronize_session=False)

        # 7. Delete session
        db.delete(session)
        db.commit()

        return {
            "success": True,
            "message": "Session and related data deleted successfully",
            "session_id": session_id,
            "documents_deleted": len(documents)
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Session deletion failed: {str(error)}"
        )
