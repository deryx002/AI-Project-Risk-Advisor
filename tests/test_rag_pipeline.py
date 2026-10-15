import sys
from pathlib import Path
from uuid import uuid4

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT_DIR / "services" / "rag-service"
DOC_DIR = ROOT_DIR / "services" / "document-service"

for mod in list(sys.modules.keys()):
    if mod == "app" or mod.startswith("app."):
        del sys.modules[mod]

sys.path = [str(RAG_DIR)] + [p for p in sys.path if p != str(DOC_DIR) and p != str(RAG_DIR)]

from app.services.chunking import chunk_text
from app.services.embeddings import generate_embedding, generate_batch_embeddings
from app.services.vector_store import (
    store_chunks,
    search_chunks,
    delete_document_chunks,
    list_indexed_documents,
)


def test_chunking_preserves_sentences():
    sample = (
        "Paragraph 1 discusses project scope and milestones.\n\n"
        "Paragraph 2 discusses software testing and risk management.\n\n"
        "Paragraph 3 discusses team resource constraints and budget."
    )
    chunks = chunk_text(sample, chunk_size=200, overlap=30)
    assert len(chunks) >= 1
    assert all(len(c) <= 250 for c in chunks)


def test_batch_embeddings():
    texts = [
        "Project delivery timeline is at risk due to critical bugs.",
        "The software architecture uses microservices and ChromaDB.",
    ]
    embeddings = generate_batch_embeddings(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 768  # nomic-embed-text dimension


def test_vector_store_store_and_search():
    doc_id = f"test_doc_{uuid4()}"
    filename = "test_project_plan.txt"
    chunks = [
        "The project delivery milestone is delayed by 2 weeks because QA testing is blocked.",
        "Frontend UI development is proceeding on schedule with React and Streamlit.",
        "Budget allocation for cloud infrastructure has been fully approved.",
    ]

    embeddings = generate_batch_embeddings(chunks)
    stored = store_chunks(
        document_id=doc_id,
        source_filename=filename,
        chunks=chunks,
        embeddings=embeddings,
    )
    assert stored == 3

    # Query for testing risks
    query = "Why is project delivery delayed?"
    q_emb = generate_embedding(query)
    results = search_chunks(q_emb, n_results=2, document_ids=[doc_id])

    assert len(results) >= 1
    top_result = results[0]
    assert "QA testing is blocked" in top_result["text"]
    assert top_result["similarity_score"] > 40.0
    assert top_result["source_filename"] == filename

    # Cleanup
    deleted = delete_document_chunks(doc_id)
    assert deleted == 3
