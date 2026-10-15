import sys
import io
from pathlib import Path
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
DOC_DIR = ROOT_DIR / "services" / "document-service"
RAG_DIR = ROOT_DIR / "services" / "rag-service"

# Evict any previous 'app' from sys.modules to avoid collision with other services
for mod in list(sys.modules.keys()):
    if mod == "app" or mod.startswith("app."):
        del sys.modules[mod]

sys.path = [str(RAG_DIR)] + [p for p in sys.path if p != str(DOC_DIR) and p != str(RAG_DIR)]

# Test RAG Service
import app.main as rag_app
rag_client = TestClient(rag_app.app)


def test_rag_batch_indexing_and_search():
    # 1. Test Batch Indexing
    payload = {
        "documents": [
            {
                "document_id": "test_batch_doc_1",
                "filename": "sprint_risk_log.txt",
                "text": "Sprint 3 is delayed because backend database migration failed with timeout errors.",
            },
            {
                "document_id": "test_batch_doc_2",
                "filename": "budget_report.txt",
                "text": "The project cloud infrastructure budget was increased by 15% to accommodate Ollama GPU inference.",
            },
        ]
    }

    res = rag_client.post("/api/rag/index-batch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_documents"] == 2
    assert data["total_chunks_indexed"] >= 2

    # 2. Test Semantic Search Endpoint
    search_payload = {
        "query": "What caused the sprint delay and migration failure?",
        "top_k": 3,
        "min_similarity": 30.0,
    }
    search_res = rag_client.post("/api/rag/search", json=search_payload)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total_results"] >= 1
    assert any("database migration failed" in r["text"] for r in search_data["results"])

    # 3. Test Documents Catalog Endpoint
    docs_res = rag_client.get("/api/rag/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()["documents"]
    doc_ids = [d["document_id"] for d in docs]
    assert "test_batch_doc_1" in doc_ids
    assert "test_batch_doc_2" in doc_ids

    # 4. Cleanup
    del_res1 = rag_client.delete("/api/rag/documents/test_batch_doc_1")
    del_res2 = rag_client.delete("/api/rag/documents/test_batch_doc_2")
    assert del_res1.status_code == 200
    assert del_res2.status_code == 200
