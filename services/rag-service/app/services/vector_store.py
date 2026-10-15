import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb

# Determine project root: .../AI Project Risk Advisor/
PROJECT_ROOT = Path(__file__).resolve().parents[4]
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

collection = client.get_or_create_collection(
    name="project_documents",
    metadata={"hnsw:space": "cosine"},
)


def delete_document_chunks(document_id: str) -> int:
    """Removes all chunks associated with a specific document_id."""
    try:
        existing = collection.get(where={"document_id": document_id})
        ids_to_delete = existing.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            return len(ids_to_delete)
        return 0
    except Exception:
        return 0


def store_chunks(
    document_id: str,
    source_filename: str,
    chunks: List[str],
    embeddings: List[List[float]],
) -> int:
    """
    Store document chunks and their embeddings into ChromaDB.
    Cleans up any existing chunks for this document_id first (deduplication).
    """
    if len(chunks) != len(embeddings):
        raise ValueError("The number of chunks must match the number of embeddings.")

    if not chunks:
        return 0

    # Clean existing chunks for this document to prevent duplicates
    delete_document_chunks(document_id)

    ids = [f"{document_id}_chunk_{index}" for index in range(len(chunks))]
    current_time = time.time()

    metadatas = [
        {
            "document_id": document_id,
            "source_filename": source_filename,
            "chunk_index": index,
            "total_chunks": len(chunks),
            "indexed_at": current_time,
        }
        for index in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(chunks)


def search_chunks(
    query_embedding: List[float],
    n_results: int = 5,
    document_ids: Optional[List[str]] = None,
    min_similarity: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Retrieve the most relevant chunks for a query embedding.
    Calculates cosine similarity percentage and supports document filtering.
    """
    if n_results <= 0:
        raise ValueError("n_results must be greater than zero.")

    if not query_embedding:
        raise ValueError("Query embedding cannot be empty.")

    total_chunks = collection.count()
    if total_chunks == 0:
        return []

    where_filter = None
    if document_ids:
        if len(document_ids) == 1:
            where_filter = {"document_id": document_ids[0]}
        else:
            where_filter = {"document_id": {"$in": document_ids}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, total_chunks),
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    matches = []
    if not results or not results["documents"] or not results["documents"][0]:
        return []

    for index, chunk in enumerate(results["documents"][0]):
        dist = results["distances"][0][index]
        # For cosine space in Chroma: distance = 1 - cosine_similarity
        # similarity = (1 - distance)
        similarity = max(0.0, round((1.0 - dist) * 100, 2))

        if similarity >= min_similarity:
            meta = results["metadatas"][0][index]
            matches.append({
                "chunk_id": results["ids"][0][index],
                "text": chunk,
                "document_id": meta.get("document_id", ""),
                "source_filename": meta.get("source_filename", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "total_chunks": meta.get("total_chunks", 1),
                "distance": round(dist, 4),
                "similarity_score": similarity,
            })

    return matches


def list_indexed_documents() -> List[Dict[str, Any]]:
    """Inspects the vector store and returns a summary of all indexed documents."""
    total = collection.count()
    if total == 0:
        return []

    results = collection.get(include=["metadatas"])
    doc_map: Dict[str, Dict[str, Any]] = {}

    for meta in results.get("metadatas", []):
        doc_id = meta.get("document_id")
        if not doc_id:
            continue
        if doc_id not in doc_map:
            doc_map[doc_id] = {
                "document_id": doc_id,
                "source_filename": meta.get("source_filename", "Unknown"),
                "chunk_count": 0,
                "indexed_at": meta.get("indexed_at", 0),
            }
        doc_map[doc_id]["chunk_count"] += 1
        if meta.get("indexed_at", 0) > doc_map[doc_id]["indexed_at"]:
            doc_map[doc_id]["indexed_at"] = meta.get("indexed_at", 0)

    return sorted(list(doc_map.values()), key=lambda x: x["indexed_at"], reverse=True)


def get_collection_stats() -> Dict[str, Any]:
    """Returns general statistics about the Chroma vector store."""
    docs = list_indexed_documents()
    return {
        "collection_name": collection.name,
        "total_chunks": collection.count(),
        "total_documents": len(docs),
        "documents": docs,
        "storage_path": str(CHROMA_DIR),
    }
