import requests
from requests.adapters import HTTPAdapter
from typing import List, Dict, Any, Optional

DOCUMENT_SERVICE_URL = "http://127.0.0.1:8000"
RAG_SERVICE_URL = "http://127.0.0.1:8002"


class RiskAdvisorAPIClient:
    """High-performance client for interacting with Document Service and RAG Service."""

    def __init__(self, doc_url: str = DOCUMENT_SERVICE_URL, rag_url: str = RAG_SERVICE_URL):
        self.doc_url = doc_url.rstrip("/")
        self.rag_url = rag_url.rstrip("/")
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)

    def check_health(self) -> Dict[str, Any]:
        """Check status of all backend microservices and Ollama with quick timeouts."""
        status = {
            "document_service": False,
            "rag_service": False,
            "ollama": False,
            "ollama_model": "None",
            "total_chunks": 0,
            "total_documents": 0,
        }

        # Check Document Service
        try:
            r = self.session.get(f"{self.doc_url}/api/health", timeout=2)
            status["document_service"] = r.status_code == 200
        except Exception:
            status["document_service"] = False

        # Check RAG Service & Stats
        try:
            r = self.session.get(f"{self.rag_url}/api/rag/stats", timeout=3)
            if r.status_code == 200:
                data = r.json()
                status["rag_service"] = True
                status["total_chunks"] = data.get("total_chunks", 0)
                status["total_documents"] = data.get("total_documents", 0)
                ollama = data.get("ollama", {})
                status["ollama"] = ollama.get("available", False)
                if ollama.get("has_embedding_model"):
                    status["ollama_model"] = "nomic-embed-text"
                elif ollama.get("models"):
                    status["ollama_model"] = ", ".join(ollama.get("models", []))
        except Exception:
            status["rag_service"] = False

        return status

    def upload_files(self, file_tuples: List[tuple]) -> Dict[str, Any]:
        """Uploads multiple files to the Document Service."""
        try:
            resp = self.session.post(
                f"{self.doc_url}/api/documents/upload",
                files=file_tuples,
                timeout=300,
            )
            return resp.json()
        except requests.RequestException as exc:
            return {
                "total_files": len(file_tuples),
                "successful": 0,
                "failed": len(file_tuples),
                "error": str(exc),
                "results": [],
            }

    def search_risks(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        min_similarity: float = 0.0,
    ) -> Dict[str, Any]:
        """Query the RAG Service vector store for relevant chunks with fast response."""
        try:
            payload = {
                "query": query,
                "top_k": top_k,
                "document_ids": document_ids,
                "min_similarity": min_similarity,
            }
            resp = self.session.post(
                f"{self.rag_url}/api/rag/search",
                json=payload,
                timeout=35,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"query": query, "total_results": 0, "results": [], "error": resp.text}
        except requests.RequestException as exc:
            return {"query": query, "total_results": 0, "results": [], "error": str(exc)}

    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        """Fetch all indexed documents from RAG Service."""
        try:
            resp = self.session.get(f"{self.rag_url}/api/rag/documents", timeout=3)
            if resp.status_code == 200:
                return resp.json().get("documents", [])
            return []
        except Exception:
            return []

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Deletes a document from both file storage and ChromaDB."""
        try:
            resp = self.session.delete(f"{self.doc_url}/api/documents/{document_id}", timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {"status": "error", "detail": resp.text}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def delete_multiple_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """Deletes multiple documents sequentially from storage and ChromaDB."""
        successful = 0
        failed = 0
        details = []

        for doc_id in document_ids:
            res = self.delete_document(doc_id)
            if res.get("status") == "deleted":
                successful += 1
            else:
                failed += 1
            details.append({"document_id": doc_id, "result": res})

        return {
            "total_requested": len(document_ids),
            "successful": successful,
            "failed": failed,
            "details": details,
        }
