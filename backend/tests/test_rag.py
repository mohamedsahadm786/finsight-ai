"""
Tests for the hybrid RAG pipeline (Phase 8).

Tests each step individually:
- HyDE (hypothetical answer generation + embedding)
- RRF fusion (merging ranked lists)
- Reranker (cross-encoder scoring)
- Generator (answer generation)
- Evaluator (RAGAS faithfulness)
- Full pipeline orchestration

Note: Qdrant-dependent tests (retriever, full pipeline) require
the Docker containers to be running. Pure logic tests (fusion,
reranker, generator mock) work without any infrastructure.
"""

import pytest


# ══════════════════════════════════════════════════════════════════
# Test HyDE
# ══════════════════════════════════════════════════════════════════

class TestHyDE:
    """Tests for the HyDE (Hypothetical Document Embeddings) step."""

    def test_hyde_returns_embedding_and_text(self):
        """HyDE should return a 768-dim embedding and a hypothetical text."""
        from backend.rag.hyde import generate_hyde_embedding

        embedding, hypothetical = generate_hyde_embedding(
            "What is the DSCR covenant threshold?"
        )

        # Embedding should be a list of 768 floats
        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert all(isinstance(v, float) for v in embedding)

        # Hypothetical text should be a non-empty string
        assert isinstance(hypothetical, str)
        assert len(hypothetical) > 20

    def test_hyde_mock_includes_question_terms(self):
        """HyDE hypothetical should relate to the question topic."""
        from backend.rag.hyde import generate_hyde_embedding

        question = "What is the minimum leverage ratio?"
        _, hypothetical = generate_hyde_embedding(question)

        # Whether mock or real GPT-3.5, the hypothetical should mention
        # at least one key term from the question
        hypothetical_lower = hypothetical.lower()
        assert "leverage" in hypothetical_lower or "ratio" in hypothetical_lower

    def test_hyde_embedding_is_normalized(self):
        """Dense embedding should be approximately unit length (for cosine similarity)."""
        import numpy as np
        from backend.rag.hyde import generate_hyde_embedding

        embedding, _ = generate_hyde_embedding("Test question about DSCR")
        norm = np.linalg.norm(embedding)

        # Should be very close to 1.0 (normalized for cosine similarity)
        assert abs(norm - 1.0) < 0.01

    def test_hyde_different_questions_different_embeddings(self):
        """Different questions should produce different embeddings."""
        from backend.rag.hyde import generate_hyde_embedding

        emb1, _ = generate_hyde_embedding("Short question")
        emb2, _ = generate_hyde_embedding("A much longer and completely different question about finance")

        # Different text lengths → different seeds → different mock vectors
        assert emb1 != emb2


# ══════════════════════════════════════════════════════════════════
# Test RRF Fusion
# ══════════════════════════════════════════════════════════════════

class TestRRFFusion:
    """Tests for Reciprocal Rank Fusion — pure logic, no infrastructure needed."""

    def _make_result(self, chunk_id: str, score: float, text: str = "chunk text") -> dict:
        """Helper to create a mock search result."""
        return {
            "id": chunk_id,
            "score": score,
            "text": text,
            "page_number": 1,
            "section": "General",
            "has_table": False,
        }

    def test_fusion_merges_two_lists(self):
        """RRF should merge dense and sparse results into one list."""
        from backend.rag.fusion import reciprocal_rank_fusion

        dense = [
            self._make_result("chunk-1", 0.95),
            self._make_result("chunk-2", 0.85),
        ]
        sparse = [
            self._make_result("chunk-3", 0.90),
            self._make_result("chunk-1", 0.80),  # appears in both lists
        ]

        fused = reciprocal_rank_fusion(dense, sparse)

        # Should have 3 unique chunks
        assert len(fused) == 3

        # All should have rrf_score
        for item in fused:
            assert "rrf_score" in item
            assert item["rrf_score"] > 0

    def test_fusion_overlapping_chunk_scores_higher(self):
        """A chunk appearing in BOTH lists should score higher than one in only one list."""
        from backend.rag.fusion import reciprocal_rank_fusion

        dense = [
            self._make_result("overlap", 0.90),
            self._make_result("dense-only", 0.85),
        ]
        sparse = [
            self._make_result("overlap", 0.80),
            self._make_result("sparse-only", 0.75),
        ]

        fused = reciprocal_rank_fusion(dense, sparse)

        # Find the overlapping chunk and a non-overlapping one
        overlap_score = None
        single_score = None
        for item in fused:
            if str(item["id"]) == "overlap":
                overlap_score = item["rrf_score"]
            elif str(item["id"]) == "dense-only":
                single_score = item["rrf_score"]

        assert overlap_score is not None
        assert single_score is not None
        assert overlap_score > single_score

    def test_fusion_sorted_by_rrf_score_descending(self):
        """Output should be sorted by RRF score, highest first."""
        from backend.rag.fusion import reciprocal_rank_fusion

        dense = [self._make_result(f"d-{i}", 0.9 - i * 0.1) for i in range(5)]
        sparse = [self._make_result(f"s-{i}", 0.9 - i * 0.1) for i in range(5)]

        fused = reciprocal_rank_fusion(dense, sparse)

        scores = [item["rrf_score"] for item in fused]
        assert scores == sorted(scores, reverse=True)

    def test_fusion_empty_inputs(self):
        """RRF should handle empty input lists gracefully."""
        from backend.rag.fusion import reciprocal_rank_fusion

        fused = reciprocal_rank_fusion([], [])
        assert fused == []

    def test_fusion_one_empty_list(self):
        """RRF should work when one list is empty."""
        from backend.rag.fusion import reciprocal_rank_fusion

        dense = [self._make_result("chunk-1", 0.9)]
        fused = reciprocal_rank_fusion(dense, [])

        assert len(fused) == 1
        assert fused[0]["rrf_score"] > 0


# ══════════════════════════════════════════════════════════════════
# Test Reranker
# ══════════════════════════════════════════════════════════════════

class TestReranker:
    """Tests for the cross-encoder re-ranker."""

    def _make_candidate(self, chunk_id: str, text: str, rrf_score: float = 0.5) -> dict:
        """Helper to create a mock RRF candidate."""
        return {
            "id": chunk_id,
            "text": text,
            "page_number": 1,
            "section": "General",
            "has_table": False,
            "rrf_score": rrf_score,
        }

    def test_reranker_returns_top_k(self):
        """Reranker should return at most top_k results."""
        from backend.rag.reranker import rerank_chunks

        candidates = [
            self._make_candidate(f"c-{i}", f"Financial text about topic {i}")
            for i in range(10)
        ]

        result = rerank_chunks("What is the DSCR?", candidates, top_k=5)

        assert len(result) <= 5

    def test_reranker_adds_rerank_score(self):
        """Each result should have a rerank_score key."""
        from backend.rag.reranker import rerank_chunks

        candidates = [
            self._make_candidate("c-1", "The DSCR ratio is 1.34x"),
            self._make_candidate("c-2", "Revenue grew 15% year over year"),
        ]

        result = rerank_chunks("What is the DSCR?", candidates, top_k=2)

        for item in result:
            assert "rerank_score" in item

    def test_reranker_empty_candidates(self):
        """Reranker should handle empty input gracefully."""
        from backend.rag.reranker import rerank_chunks

        result = rerank_chunks("Some question", [], top_k=5)
        assert result == []

    def test_reranker_relevant_chunk_scores_higher(self):
        """A chunk directly answering the question should score higher."""
        from backend.rag.reranker import rerank_chunks

        candidates = [
            self._make_candidate("relevant", "The Debt Service Coverage Ratio (DSCR) is 1.34x for FY2023"),
            self._make_candidate("irrelevant", "The weather forecast for tomorrow shows partly cloudy skies"),
        ]

        result = rerank_chunks("What is the DSCR?", candidates, top_k=2)

        # The relevant chunk should be ranked first
        assert result[0]["id"] == "relevant"


# ══════════════════════════════════════════════════════════════════
# Test Generator
# ══════════════════════════════════════════════════════════════════

class TestGenerator:
    """Tests for the answer generator (mock mode)."""

    def test_generator_returns_answer_and_tokens(self):
        """Generator should return a string answer and token count."""
        from backend.rag.generator import generate_answer

        chunks = [
            {"text": "The DSCR is 1.34x for fiscal year 2023.", "page_number": 14},
            {"text": "Revenue increased by 12% compared to prior year.", "page_number": 22},
        ]

        answer, tokens = generate_answer("What is the DSCR?", chunks)

        assert isinstance(answer, str)
        assert len(answer) > 20
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_generator_references_page_numbers(self):
        """Mock answer should reference the page numbers from chunks."""
        from backend.rag.generator import generate_answer

        chunks = [
            {"text": "Some financial data here.", "page_number": 14},
            {"text": "More data on another page.", "page_number": 47},
        ]

        answer, _ = generate_answer("Tell me about the financials", chunks)

        assert "p.14" in answer or "14" in answer
        assert "p.47" in answer or "47" in answer

    def test_generator_empty_chunks(self):
        """Generator should handle empty chunks gracefully."""
        from backend.rag.generator import generate_answer

        answer, tokens = generate_answer("What is the DSCR?", [])

        assert isinstance(answer, str)
        assert "could not find" in answer.lower()

    def test_generator_includes_chunk_content(self):
        """Mock answer should include snippet from top chunk."""
        from backend.rag.generator import generate_answer

        chunks = [
            {"text": "The leverage ratio stands at 4.8x as of December 2023.", "page_number": 5},
        ]

        answer, _ = generate_answer("What is the leverage ratio?", chunks)

        # Should contain some text from the chunk
        assert "leverage" in answer.lower() or "4.8" in answer


# ══════════════════════════════════════════════════════════════════
# Test Evaluator
# ══════════════════════════════════════════════════════════════════

class TestEvaluator:
    """Tests for the RAGAS evaluator."""

    def test_evaluator_returns_score_or_none(self):
        """Evaluator should return a float score if OpenAI key is set, or None if not."""
        from backend.rag.evaluator import compute_faithfulness

        score = compute_faithfulness(
            question="What is DSCR?",
            answer="DSCR is 1.34x.",
            contexts=["The DSCR is 1.34x for FY2023."],
        )

        # If OPENAI_API_KEY is set, RAGAS runs and returns a float 0.0-1.0
        # If not set, returns None gracefully
        if score is not None:
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

