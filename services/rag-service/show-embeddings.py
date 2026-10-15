
from app.services.vector_store import collection


def show_embeddings():
    results = collection.get(
        include=["documents", "metadatas", "embeddings"]
    )

    ids = results["ids"]
    documents = results["documents"]
    metadatas = results["metadatas"]
    embeddings = results["embeddings"]

    print("Total indexed chunks:", len(ids))

    if not ids:
        print("No chunks found in the collection.")
        return

    for i, chunk_id in enumerate(ids):
        print("\n" + "=" * 60)
        print("Chunk ID:", chunk_id)
        print("Metadata:", metadatas[i])
        print("Stored text:", documents[i])

        vector = embeddings[i].tolist()
        print("Embedding dimensions:", len(vector))
        print("First 10 embedding values:", vector[:10])


if __name__ == "__main__":
    show_embeddings()
