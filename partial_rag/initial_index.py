import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# === Load dataset ===
with open("test_data.json", "r") as f:
    data = json.load(f)

# === Prepare email texts and IDs ===
texts = [item["subject"] + " " + item["body"] for item in data]
labels = [item["label"] for item in data]
ids = np.arange(len(texts))  # numeric IDs 0..99

# === Load embedding model ===
model = SentenceTransformer("all-MiniLM-L6-v2")

# === Generate & normalize embeddings ===
embeddings = model.encode(texts, convert_to_numpy=True)
embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)  # normalize manually

dimension = embeddings.shape[1]

# === Create FAISS index (Cosine similarity using Inner Product) ===
index = faiss.IndexFlatIP(dimension)  # Inner Product = cosine similarity (for normalized vectors)
index = faiss.IndexIDMap(index)

# Add vectors + IDs
index.add_with_ids(embeddings, ids)

# === Save index and metadata ===
faiss.write_index(index, "email_index.faiss")

metadata = [
    {
        "id": int(ids[i]),
        "subject": data[i]["subject"],
        "body": data[i]["body"],
        "label": data[i]["label"]
    }
    for i in range(len(data))
]

with open("metadata.json", "w") as f:
    json.dump(metadata, f, indent=4)

print("✅ FAISS index and metadata created successfully!")
print(f"Total entries indexed: {index.ntotal}")
