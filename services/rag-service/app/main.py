from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.indexing import router as indexing_router
from app.routes.retrieval import router as retrieval_router

app = FastAPI(
    title="AI Project Risk Advisor - RAG Service",
    description="Document chunking, embedding, indexing, vector storage, and semantic retrieval",
    version="0.2.0",
)

# Enable CORS for direct access from frontend or gateways
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "service": "RAG Service",
        "version": "0.2.0",
        "status": "running",
        "endpoints": [
            "/api/health",
            "/api/rag/index",
            "/api/rag/index-batch",
            "/api/rag/search",
            "/api/rag/documents",
            "/api/rag/stats",
        ],
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


app.include_router(indexing_router)
app.include_router(retrieval_router)
