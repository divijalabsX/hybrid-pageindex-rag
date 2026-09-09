from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load all SQLAlchemy models before loading API routes.
# This ensures all foreign-key target tables are registered
# in Base.metadata.
from app.models.user import User
from app.models.llm_config import LLMConfig
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.processing_job import ProcessingJob
from app.models.conversation import Conversation
from app.models.message import Message

from app.api.routes import router
from app.api.document_routes import router as document_router
from app.api.user_routes import router as user_router

from app.api.llm_config_routes import router as llm_config_router
from app.api.document_chunk_routes import router as chunk_router
from app.api.processing_job_routes import router as job_router
from app.api.conversation_routes import router as conversation_router
from app.api.message_routes import router as message_router


app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware 


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(user_router)
app.include_router(document_router)
app.include_router(llm_config_router)
app.include_router(chunk_router)
app.include_router(job_router)
app.include_router(conversation_router)
app.include_router(message_router)


@app.get("/")
def read_root():
    return {
        "message": "Hybrid PageIndex RAG API is running"
    }