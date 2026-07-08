"""
One-time (or re-run-when-docs-change) script: embeds every markdown file
in docs/ and stores the vectors in a local ChromaDB collection.

This is NOT called by the agent at query time — it's an offline indexing
step you run manually whenever you add/edit docs. The agent only ever
calls search_docs.py at query time, which reads the pre-built index.

Usage:
    python src/rag/index_docs.py
"""

import glob
import os
import re
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types
import chromadb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rag.config import DOCS_DIR, CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL, EMBED_DIM

load_dotenv()


def chunk_markdown(text: str) -> list[str]:
    """Split a markdown doc into chunks at each '## ' section heading.
    Keeps the '# Title' line attached to the first section."""
    parts = re.split(r"\n(?=## )", text)
    return [p.strip() for p in parts if p.strip()]


def build_index():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set. Copy .env.example to .env and add your key.", file=sys.stderr)
        sys.exit(1)

    genai_client = genai.Client(api_key=api_key)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Fresh rebuild every time — simplest correct behavior for a small doc set.
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = chroma_client.create_collection(COLLECTION_NAME)

    ids, docs, metadatas = [], [], []
    filepaths = sorted(glob.glob(os.path.join(DOCS_DIR, "*.md")))
    if not filepaths:
        print(f"No .md files found in {DOCS_DIR}", file=sys.stderr)
        sys.exit(1)

    for filepath in filepaths:
        source = os.path.basename(filepath)
        with open(filepath, "r") as f:
            text = f.read()
        for i, chunk in enumerate(chunk_markdown(text)):
            ids.append(f"{source}-{i}")
            docs.append(chunk)
            metadatas.append({"source": source})

    print(f"Embedding {len(docs)} chunks from {len(filepaths)} files...")
    result = genai_client.models.embed_content(
        model=EMBED_MODEL,
        contents=docs,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT", output_dimensionality=EMBED_DIM
        ),
    )
    embeddings = [e.values for e in result.embeddings]

    collection.add(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeddings)
    print(f"Indexed {len(docs)} chunks into '{COLLECTION_NAME}' at {CHROMA_DIR}")


if __name__ == "__main__":
    build_index()