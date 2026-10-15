
from app.services.embeddings import generate_embedding

text = "The project delivery is delayed because testing is incomplete."

embedding = generate_embedding(text)

print("Embedding generated successfully!")
print("Vector dimensions:", len(embedding))
print("First 5 values:", embedding[:5])
