"""
Skill: search_docs

Embeds the query, searches the pre-built ChromaDB index (see
index_docs.py), and returns the most relevant doc chunks.

This is the RAG "R" — retrieval. The agent calls this, gets back
grounded text from your own docs, and uses it to inform its final
answer instead of relying purely on the model's training data.
"""

import os
import sys

from google import genai
from google.genai import types
import chromadb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models import DocChunk
from rag.config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL, EMBED_DIM


def search_docs(query: str, n_results: int = 3) -> list[DocChunk]:
    """
    Args:
        query: natural language question, e.g. "why does refresh token return None"
        n_results: how many chunks to return

    Returns:
        List[DocChunk], most relevant first
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    genai_client = genai.Client(api_key=api_key)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        collection = chroma_client.get_collection(COLLECTION_NAME)
    except Exception:
        print(
            f"No index found at {CHROMA_DIR}. Run `python src/rag/index_docs.py` first.",
            file=sys.stderr,
        )
        sys.exit(1)

    result = genai_client.models.embed_content(
        model=EMBED_MODEL,
        contents=query,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY", output_dimensionality=EMBED_DIM
        ),
    )
    query_embedding = result.embeddings[0].values

    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        chunks.append(DocChunk(text=doc, source=meta["source"], score=dist))
    return chunks