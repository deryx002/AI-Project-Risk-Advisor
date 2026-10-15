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

sys.path = [str(DOC_DIR)] + [p for p in sys.path if p != str(DOC_DIR) and p != str(RAG_DIR)]
import app.main as doc_app
doc_client = TestClient(doc_app.app)


def test_batch_upload_twelve_files():
    # Prepare 12 mock project files
    files_payload = []
    for i in range(1, 13):
        content = f"Project Document #{i}: Sprint update and risk tracking notes for milestone {i}. Testing is scheduled."
        file_tuple = (
            "files",
            (f"project_doc_{i}.txt", io.BytesIO(content.encode("utf-8")), "text/plain"),
        )
        files_payload.append(file_tuple)

    # Send multi-file upload
    response = doc_client.post("/api/documents/upload", files=files_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["total_files"] == 12
    assert data["successful"] == 12
    assert data["failed"] == 0
    assert len(data["results"]) == 12

    # Check first result fields
    first_result = data["results"][0]
    assert first_result["filename"] == "project_doc_1.txt"
    assert first_result["file_type"] == "txt"
    assert first_result["character_count"] > 0
    assert "document_id" in first_result

    # Cleanup created test files from data/uploads
    for res in data["results"]:
        doc_id = res["document_id"]
        doc_client.delete(f"/api/documents/{doc_id}")
