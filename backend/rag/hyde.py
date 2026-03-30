"""
HyDE — Hypothetical Document Embeddings.

Step 1 of the RAG pipeline.

Problem: A short user question like "What is the DSCR threshold?" has a very
different embedding from the document chunk that contains the answer:
"The Debt Service Coverage Ratio shall not fall below 1.20x per Section 7.1."

Solution: Ask GPT-3.5-turbo to generate a FAKE hypothetical answer that
sounds like financial document language. Embed THAT hypothetical answer
(not the original question) and use it as the dense search query.

The hypothetical answer doesn't need to be factually correct — it just needs
to sound like the kind of text that would appear in a financial document,
so its embedding lands close to the real answer chunk in vector space.

Cost: ~$0.001 per query using GPT-3.5-turbo.
Locally: GPT-3.5 call is mocked if OPENAI_API_KEY is empty.
         Dense embedding is mocked (same as Agent 1).
"""

import logging

import numpy as np

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Generate hypothetical answer using GPT-3.5-turbo
# ---------------------------------------------------------------------------
HYDE_SYSTEM_PROMPT = (
    "You are a financial document assistant. Given a user question about a "
    "financial document (annual report, credit agreement, earnings call), "
    "write a short hypothetical answer (2-3 sentences) that sounds like it "
    "came directly from that document. Use formal financial language. "
    "The answer does NOT need to be factually correct — it just needs to "
    "sound like real financial document text so we can use it for search."
)


def _generate_hypothetical_answer(question: str) -> str:
    """
    Call GPT-3.5-turbo to generate a hypothetical document-style answer.

    If OPENAI_API_KEY is empty (local dev), returns a mock hypothetical answer.
    """
    if not settings.OPENAI_API_KEY:
        # Mock mode — return a simple hypothetical that includes the question terms
        logger.info("HyDE: OPENAI_API_KEY not set, using mock hypothetical answer")
        return (
            f"Based on the financial statements and covenant requirements, "
            f"the analysis indicates that {question} The relevant metrics "
            f"and financial ratios are disclosed in the accompanying notes "
            f"to the consolidated financial statements for the fiscal year."
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": HYDE_SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0.7,
            max_tokens=150,
        )
        hypothetical = response.choices[0].message.content.strip()
        logger.info(f"HyDE: Generated hypothetical answer ({len(hypothetical)} chars)")
        return hypothetical

    except Exception as e:
        logger.error(f"HyDE: GPT-3.5 call failed: {e}. Using mock fallback.")
        return (
            f"Based on the financial statements and covenant requirements, "
            f"the analysis indicates that {question} The relevant metrics "
            f"and financial ratios are disclosed in the accompanying notes "
            f"to the consolidated financial statements for the fiscal year."
        )


# ---------------------------------------------------------------------------
# Embed the hypothetical answer — same approach as Agent 1
# ---------------------------------------------------------------------------
def _embed_hypothetical(text: str) -> list[float]:
    """
    Generate a 768-dim dense embedding for the hypothetical answer.

    Uses the EXACT same embedding logic as Agent 1's _generate_dense_embedding
    so that the query vector lives in the same vector space as the indexed chunks.

    Locally: deterministic pseudo-random vector based on text length.
    EC2: real BAAI/bge-base-financial-matryoshka model.
    """
    if settings.USE_REAL_LLAMA:
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("BAAI/bge-base-financial-matryoshka")
            embedding = model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"HyDE: Real embedding failed: {e}. Falling back to mock.")

    # Mock embedding — MUST match Agent 1's mock logic exactly
    rng = np.random.RandomState(seed=len(text) % 10000)
    vec = rng.randn(768).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


# ---------------------------------------------------------------------------
# Public function — called by the RAG service
# ---------------------------------------------------------------------------
def generate_hyde_embedding(question: str) -> tuple[list[float], str]:
    """
    Full HyDE step: question → hypothetical answer → dense embedding.

    Returns:
        tuple of (embedding_vector, hypothetical_answer_text)
        - embedding_vector: 768-dim list[float] for Qdrant dense search
        - hypothetical_answer_text: the generated text (logged for debugging)
    """
    logger.info(f"HyDE: Processing question: '{question[:80]}...'")

    # Step 1: Generate hypothetical answer
    hypothetical = _generate_hypothetical_answer(question)

    # Step 2: Embed the hypothetical answer
    embedding = _embed_hypothetical(hypothetical)

    logger.info(f"HyDE: Embedding generated (dim={len(embedding)})")
    return embedding, hypothetical