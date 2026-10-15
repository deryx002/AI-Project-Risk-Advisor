
from uuid import uuid4

from app.services.chunking import chunk_text
from app.services.embeddings import generate_embedding
from app.services.vector_store import store_chunks, search_chunks


document_id = str(uuid4())
filename = "sample_project.txt"

sample_text = """
The project deadline is approaching.
Software testing is incomplete and may delay delivery.
The project team must resolve testing blockers.
The project budget is approved.
"""

# 1. Split the document into chunks
chunks = chunk_text(sample_text, chunk_size=150, overlap=20)

# 2. Generate an embedding for every chunk
embeddings = [generate_embedding(chunk) for chunk in chunks]

# 3. Store the chunks and embeddings
stored_count = store_chunks(
    document_id=document_id,
    source_filename=filename,
    chunks=chunks,
    embeddings=embeddings,
)

print("Chunks stored:", stored_count)

# 4. Search using a question
question = "What could delay project delivery?"
query_embedding = generate_embedding(question)

matches = search_chunks(query_embedding, n_results=3)

print("\nSearch results:")

for match in matches:
    print("\nText:", match["text"])
    print("Source:", match["metadata"]["source_filename"])
    print("Distance:", round(match["distance"], 4))
