"""Shared constants for the RAG pipeline. Kept in one place so
index_docs.py (run once, offline) and search_docs.py (run per query)
never drift out of sync on model name or dimensionality.
"""

import os

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
COLLECTION_NAME = "devops_docs"
EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768