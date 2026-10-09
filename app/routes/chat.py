
import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.db.database import get_db
from app.models.chat import Chat
from app.models.session import ChatSession
from app.models.chat_request import ChatRequest
from app.services.data_retrieval import retrieve_chunks

load_dotenv()

router = APIRouter()

# Initialize LLM
llm = ChatGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
    model="openai/gpt-oss-120b",
    temperature=0.2
)

# Prompt template
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a document question-answering assistant.

        Rules:
        1. Answer using only the provided document context.
        2. Do not invent facts or information.
        3. If the answer is not available in the context, say:
           "I couldn't find this information in the uploaded documents."
        4. Do not fabricate citations.
        """
    ),
    (
        "human",
        """Document context:
{context}

User question:
{question}

Answer the question using the provided context."""
    )
])


@router.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    try:
        # 1. Validate session
        session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )

        # 2. Retrieve top 5 relevant chunks
        chunks = retrieve_chunks(
            query=request.question,
            session_id=request.session_id,
            k=5
        )

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail="No relevant document chunks found for this session"
            )

        # 3. Prepare document context
        context = "\n\n".join(
            f"Source: {chunk['filename']}, "
            f"Page: {chunk['page']}, "
            f"Chunk: {chunk['chunk_index']}\n"
            f"{chunk['content']}"
            for chunk in chunks
        )

        # 4. Generate answer
        chain = prompt | llm

        response = chain.invoke({
            "context": context,
            "question": request.question
        })

        answer = response.content

        # 5. Prepare citations
        citations = [
            {
                "filename": chunk["filename"],
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"]
            }
            for chunk in chunks
        ]

        # 6. Save conversation to SQLite
        user_message = Chat(
            session_id=request.session_id,
            role="user",
            content=request.question
        )

        assistant_message = Chat(
            session_id=request.session_id,
            role="assistant",
            content=answer
        )

        db.add_all([user_message, assistant_message])
        db.commit()

        # 7. Return response
        return {
            "success": True,
            "session_id": request.session_id,
            "question": request.question,
            "answer": answer,
            "citations": citations
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(error)}"
        )
