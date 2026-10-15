
from app.services.chunking import chunk_text

sample_text = "Project risks and deliverables. " * 100

chunks = chunk_text(sample_text)

print("Original characters:", len(sample_text))
print("Number of chunks:", len(chunks))

for index, chunk in enumerate(chunks, start=1):
    print(f"Chunk {index}: {len(chunk)} characters")
