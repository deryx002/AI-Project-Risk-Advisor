from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.chunking import chunk_text
from app.services.embeddings import generate_batch_embeddings, check_ollama_status
from app.services.vector_store import (
    store_chunks,
    delete_document_chunks,
    list_indexed_documents,
    get_collection_stats,
)

router = APIRouter(prefix="/api/rag", tags=["RAG-Indexing"])


class IndexDocumentRequest(BaseModel):
    document_id: str
    filename: str
    text: str
    file_hash: Optional[str] = None


class BatchIndexRequest(BaseModel):
    documents: List[IndexDocumentRequest]


@router.post("/index")
def index_document(request: IndexDocumentRequest):
    """Indexes a single document into the vector store."""
    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Document text cannot be empty.",
        )

    try:
        chunks = chunk_text(request.text, chunk_size=1000, overlap=150)
        embeddings = generate_batch_embeddings(chunks)

        stored_count = store_chunks(
            document_id=request.document_id,
            source_filename=request.filename,
            chunks=chunks,
            embeddings=embeddings,
        )

        return {
            "document_id": request.document_id,
            "filename": request.filename,
            "chunks_indexed": stored_count,
            "status": "indexed",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document indexing failed: {exc}",
        ) from exc


@router.post("/index-batch")
def index_documents_batch(request: BatchIndexRequest):
    """
    Indexes multiple documents in batch. Uses optimized batch embeddings
    and deduplicates by document_id.
    """
    if not request.documents:
        raise HTTPException(status_code=400, detail="Document list cannot be empty.")

    results = []
    total_chunks_indexed = 0

    for doc in request.documents:
        if not doc.text.strip():
            results.append({
                "document_id": doc.document_id,
                "filename": doc.filename,
                "status": "skipped",
                "detail": "Empty text",
                "chunks_indexed": 0,
            })
            continue

        try:
            chunks = chunk_text(doc.text, chunk_size=1000, overlap=150)
            if not chunks:
                results.append({
                    "document_id": doc.document_id,
                    "filename": doc.filename,
                    "status": "skipped",
                    "detail": "No valid chunks extracted",
                    "chunks_indexed": 0,
                })
                continue

            embeddings = generate_batch_embeddings(chunks)
            stored_count = store_chunks(
                document_id=doc.document_id,
                source_filename=doc.filename,
                chunks=chunks,
                embeddings=embeddings,
            )
            total_chunks_indexed += stored_count

            results.append({
                "document_id": doc.document_id,
                "filename": doc.filename,
                "chunks_indexed": stored_count,
                "status": "indexed",
            })

        except Exception as exc:
            results.append({
                "document_id": doc.document_id,
                "filename": doc.filename,
                "status": "error",
                "detail": str(exc),
                "chunks_indexed": 0,
            })

    return {
        "total_documents": len(request.documents),
        "total_chunks_indexed": total_chunks_indexed,
        "results": results,
    }


@router.get("/documents")
def get_indexed_documents():
    """Lists all indexed documents and their chunk counts in ChromaDB."""
    documents = list_indexed_documents()
    return {
        "total_documents": len(documents),
        "documents": documents,
    }


@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    """Removes a document and its chunks from the Chroma vector store."""
    deleted_count = delete_document_chunks(document_id)
    if deleted_count == 0:
        return {"document_id": document_id, "deleted_chunks": 0, "message": "Document not found in index"}
    return {
        "document_id": document_id,
        "deleted_chunks": deleted_count,
        "status": "deleted",
    }


@router.get("/stats")
def get_stats():
    """Returns vector store and Ollama model status."""
    ollama_info = check_ollama_status()
    stats = get_collection_stats()
    stats["ollama"] = ollama_info
    return stats
