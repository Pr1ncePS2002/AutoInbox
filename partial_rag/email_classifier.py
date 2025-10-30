import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import os
from config.settings import RAG_SETTINGS
from llm_utils.classifier import categorize_email

# INITIAL SETUP
model = SentenceTransformer(RAG_SETTINGS.get('MODEL_NAME','all-MiniLM-L6-v2'))

# Load FAISS index if exists, else create new
if os.path.exists(RAG_SETTINGS.get('INDEX_PATH')):
    index = faiss.read_index(RAG_SETTINGS.get('INDEX_PATH'))
    print(f"✅ Loaded existing FAISS index with {index.ntotal} entries.")
else:
    index = faiss.IndexFlatIP(384)  # Inner Product for cosine similarity
    index = faiss.IndexIDMap(index)
    print("⚙️ Created new FAISS index (cosine similarity).")

# Load metadata if exists
if os.path.exists(RAG_SETTINGS.get('METADATA_PATH')):
    with open(RAG_SETTINGS.get('METADATA_PATH'), "r") as f:
        metadata = json.load(f)
else:
    metadata = []

next_id = max([m["id"] for m in metadata], default=-1) + 1

# FUNCTION: CLASSIFY OR ADD MAIL
def classify_(subject: str, body: str):
    global next_id, metadata

    text = subject + " " + body
    embedding = model.encode([text], convert_to_numpy=True)
    embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)  # normalize

    if index.ntotal > 0:
        D, I = index.search(embedding, k=1)
        similarity = D[0][0]  # cosine similarity directly
        print(f"🔍 Similarity score: {similarity:.3f}")

        if similarity >= RAG_SETTINGS.get('SIMILARITY_THRESHOLD','0.75'):
            matched_id = int(I[0][0])
            matched_label = next((m["label"] for m in metadata if m["id"] == matched_id), None)
            print(f"✅ Similar mail found → Label: {matched_label}")
            return matched_label

    print("⚠️ No similar mail found → Adding to index.")
    new_id = next_id
    index.add_with_ids(embedding, np.array([new_id]))
    label=categorize_email(subject=subject,body=body)
    metadata.append({
        "id": new_id,
        "subject": subject,
        "label": label
    })
    next_id += 1

    return label

# FUNCTION: SAVE INDEX + METADATA
def save_index():
    faiss.write_index(index, RAG_SETTINGS.get('INDEX_PATH'))
    with open(RAG_SETTINGS.get('METADATA_PATH'), "w") as f:
        json.dump(metadata, f, indent=4)
    print("💾 Index and metadata saved successfully.")

# # Example usage
# if __name__ == "__main__":
#     label = classify_or_add(
#         subject="Buy one get 3 free",
#         body="If you buy 1 toothpaste , get 3 brush free"
#     )
#     print("Returned Label:", label)
#     save_index()
