
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.upload import router as upload_router
from app.routes.chat import router as chat_router
from app.routes.deletesession import router as delete_session_router

from app.db.database import engine, Base
from app.models.session import ChatSession
from app.models.document import Document
from app.models.chat import Chat

# Create SQLite tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Intern Assignment API",
    description="API for the Intern Assignment",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(delete_session_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}
