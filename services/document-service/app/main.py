import hashlib
import os
import time
from pathlib import Path
from uuid import uuid5, NAMESPACE_DNS
from typing import List

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    UPLOAD_DIR,
    MAX_FILE_SIZE_MB,
    MAX_BATCH_FILES,
    ALLOWED_EXTENSIONS,
)
from app.services.ingestion import extract_text

app = FastAPI(
    title="AI Project Intelligence & Risk Advisor - Document Service",
    description="Multi-file document upload, validation, text extraction and RAG forwarding",
    version="0.2.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
RAG_BATCH_INDEX_URL = "http://127.0.0.1:8002/api/rag/index-batch"
RAG_DOCS_URL = "http://127.0.0.1:8002/api/rag/documents"


@app.get("/")
def home():
    return {
        "service": "Document Service",
        "version": "0.2.0",
        "status": "running",
        "max_batch_files": MAX_BATCH_FILES,
        "max_file_size_mb": MAX_FILE_SIZE_MB,
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Accepts 1 to 50+ files concurrently (PDF, DOCX, CSV, TXT),
    validates them, computes SHA-256 deduplication fingerprints,
    extracts text, and sends them in batch to the RAG Service.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Exceeded maximum batch limit of {MAX_BATCH_FILES} files.",
        )

    processed_documents = []
    extraction_results = []

    for file in files:
        raw_filename = file.filename or "unnamed_document"
        filename = Path(raw_filename).name
        extension = Path(filename).suffix.lower()

        # 1. Extension Validation
        if extension not in ALLOWED_EXTENSIONS:
            extraction_results.append({
                "filename": filename,
                "status": "error",
                "detail": f"Unsupported format. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            })
            await file.close()
            continue

        temp_path = UPLOAD_DIR / f"temp_{int(time.time() * 1000)}_{filename}"
        hasher = hashlib.sha256()
        total_size = 0

        try:
            # 2. Stream File & Compute Hash
            with temp_path.open("wb") as destination:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit.",
                        )
                    hasher.update(chunk)
                    destination.write(chunk)

            file_hash = hasher.hexdigest()
            # Deterministic document_id from hash
            document_id = str(uuid5(NAMESPACE_DNS, file_hash))
            final_saved_path = UPLOAD_DIR / f"{document_id}_{filename}"

            # Rename or replace with clean deterministic path
            if final_saved_path.exists():
                temp_path.unlink(missing_ok=True)
            else:
                temp_path.replace(final_saved_path)

            # 3. Extract Text
            text = extract_text(final_saved_path)

            processed_documents.append({
                "document_id": document_id,
                "filename": filename,
                "file_hash": file_hash,
                "file_type": extension.lstrip("."),
                "size_bytes": total_size,
                "character_count": len(text),
                "text": text,
            })

            extraction_results.append({
                "document_id": document_id,
                "filename": filename,
                "file_type": extension.lstrip("."),
                "size_bytes": total_size,
                "character_count": len(text),
                "status": "extracted",
            })

        except HTTPException as exc:
            temp_path.unlink(missing_ok=True)
            extraction_results.append({
                "filename": filename,
                "status": "error",
                "detail": exc.detail,
            })
        except Exception as exc:
            temp_path.unlink(missing_ok=True)
            extraction_results.append({
                "filename": filename,
                "status": "error",
                "detail": f"Extraction failed: {str(exc)}",
            })
        finally:
            await file.close()

    # 4. Forward successfully extracted documents to RAG Service in Batch
    indexing_summary = {"status": "skipped", "indexed_documents": 0}
    if processed_documents:
        rag_payload = {
            "documents": [
                {
                    "document_id": doc["document_id"],
                    "filename": doc["filename"],
                    "text": doc["text"],
                    "file_hash": doc["file_hash"],
                }
                for doc in processed_documents
            ]
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(RAG_BATCH_INDEX_URL, json=rag_payload)
                response.raise_for_status()
                indexing_summary = response.json()

                # Merge RAG indexing results into file reports
                indexed_map = {
                    item["document_id"]: item
                    for item in indexing_summary.get("results", [])
                }
                for item in extraction_results:
                    doc_id = item.get("document_id")
                    if doc_id and doc_id in indexed_map:
                        item["status"] = "indexed"
                        item["chunks_indexed"] = indexed_map[doc_id].get("chunks_indexed", 0)

            except httpx.RequestError as exc:
                for item in extraction_results:
                    if item.get("status") == "extracted":
                        item["status"] = "warning"
                        item["detail"] = (
                            "Extracted and saved locally, but RAG indexing failed. "
                            f"Check if RAG service is running on port 8002 ({str(exc)})."
                        )

    successful_count = sum(1 for item in extraction_results if item.get("status") in ("indexed", "extracted", "warning"))
    failed_count = sum(1 for item in extraction_results if item.get("status") == "error")

    return {
        "total_files": len(files),
        "successful": successful_count,
        "failed": failed_count,
        "results": extraction_results,
        "rag_summary": indexing_summary,
    }


@app.get("/api/documents")
def list_uploaded_documents():
    """Returns all files currently saved in the uploads directory."""
    files = []
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file() and not file_path.name.startswith("temp_"):
            stat = file_path.stat()
            # Extract document_id and filename
            parts = file_path.name.split("_", 1)
            doc_id = parts[0] if len(parts) > 1 else file_path.stem
            orig_name = parts[1] if len(parts) > 1 else file_path.name
            files.append({
                "document_id": doc_id,
                "filename": orig_name,
                "stored_filename": file_path.name,
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
                "extension": file_path.suffix.lstrip("."),
            })
    return {"total_files": len(files), "documents": sorted(files, key=lambda x: x["modified_at"], reverse=True)}


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Deletes uploaded document from storage and tells RAG service to drop its vectors."""
    matched_files = list(UPLOAD_DIR.glob(f"{document_id}*"))
    deleted_local = False
    for path in matched_files:
        path.unlink(missing_ok=True)
        deleted_local = True

    # Call RAG service to drop vectors
    rag_deleted = False
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.delete(f"{RAG_DOCS_URL}/{document_id}")
            if resp.status_code == 200:
                rag_deleted = True
        except Exception:
            pass

    return {
        "document_id": document_id,
        "deleted_local_file": deleted_local,
        "deleted_rag_vectors": rag_deleted,
        "status": "deleted" if (deleted_local or rag_deleted) else "not_found",
    }
