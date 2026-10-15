from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.embeddings import generate_embedding
from app.services.vector_store import search_chunks

router = APIRouter(prefix="/api/rag", tags=["RAG-Retrieval"])


class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query or question")
    top_k: int = Field(5, ge=1, le=25, description="Number of top chunks to retrieve")
    document_ids: Optional[List[str]] = Field(None, description="Optional document IDs to filter search")
    min_similarity: Optional[float] = Field(0.0, ge=0.0, le=100.0, description="Minimum similarity percentage (0-100)")


class ChunkResult(BaseModel):
    chunk_id: str
    text: str
    document_id: str
    source_filename: str
    chunk_index: int
    total_chunks: int
    distance: float
    similarity_score: float


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[ChunkResult]


@router.post("/search", response_model=SearchResponse)
def search_similar_chunks(request: SearchRequest):
    """
    Retrieves the most semantically relevant chunks across indexed project documents
    for a given natural-language query.
    """
    cleaned_query = request.query.strip()
    if not cleaned_query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    try:
        # 1. Generate query embedding vector using Ollama
        query_embedding = generate_embedding(cleaned_query)

        # 2. Query ChromaDB vector store
        matches = search_chunks(
            query_embedding=query_embedding,
            n_results=request.top_k,
            document_ids=request.document_ids,
            min_similarity=request.min_similarity or 0.0,
        )

        return SearchResponse(
            query=cleaned_query,
            total_results=len(matches),
            results=[ChunkResult(**m) for m in matches],
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Semantic retrieval failed: {str(exc)}",
        ) from exc
