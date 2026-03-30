"""
RAG (Retrieval-Augmented Generation) package.

Contains the 5-step hybrid RAG pipeline:
1. hyde.py       — HyDE hypothetical document embeddings
2. retriever.py  — Hybrid Qdrant search (dense + sparse)
3. fusion.py     — Reciprocal Rank Fusion (RRF)
4. reranker.py   — Cross-encoder re-ranking
5. generator.py  — Answer generation (LLaMA / mock)
6. evaluator.py  — RAGAS quality evaluation
"""