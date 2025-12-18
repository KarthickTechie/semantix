import json
import os

def load_rag_data():
    file_path = os.path.join("data", "cif_data.json")
    with open(file_path, "r") as f:
        return json.load(f)

RAG_DATA = load_rag_data()
