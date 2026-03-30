"""
Answer Generator.

Step 5 of the RAG pipeline.

Takes the original user question + top 5 re-ranked chunks and generates
a grounded answer.

Locally (USE_REAL_LLAMA=false): Returns a mock answer that references
the actual chunk content (so we can verify the pipeline works end-to-end).

On EC2 (USE_REAL_LLAMA=true): Sends the question + chunks to the
fine-tuned LLaMA model for real generation.

The generated answer must ONLY use information from the provided chunks.
This is enforced by the prompt — the model is told not to use outside knowledge.
"""

import logging
from typing import Any

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Generation prompt template
# ---------------------------------------------------------------------------
GENERATION_SYSTEM_PROMPT = (
    "You are a financial document analyst. Answer the user's question "
    "using ONLY the information from the provided document excerpts below. "
    "If the excerpts do not contain enough information to answer, say so. "
    "Do NOT use any outside knowledge. Cite the page numbers when possible."
)

GENERATION_CONTEXT_TEMPLATE = """Document excerpts:

{context}

---
Question: {question}

Answer based ONLY on the excerpts above:"""


# ---------------------------------------------------------------------------
# Mock answer generation (local development)
# ---------------------------------------------------------------------------
def _mock_generate_answer(
    question: str,
    chunks: list[dict[str, Any]],
) -> tuple[str, int]:
    """
    Generate a mock answer that references real chunk content.

    Returns (answer_text, tokens_used).
    """
    if not chunks:
        return (
            "I could not find relevant information in the document to answer "
            "your question. Please try rephrasing or ask about a different topic.",
            50,
        )

    # Build a mock answer using actual chunk snippets
    page_refs = sorted(set(c.get("page_number", 0) for c in chunks))
    page_str = ", ".join(f"p.{p}" for p in page_refs if p > 0)

    # Take first 200 chars of the top chunk as a reference
    top_chunk_preview = chunks[0].get("text", "")[:200]

    answer = (
        f"Based on the document analysis (sources: {page_str}), "
        f"the relevant information indicates: \"{top_chunk_preview}...\" "
        f"This information was extracted from {len(chunks)} relevant sections "
        f"of the document. [Mock answer — real LLaMA generation on EC2]"
    )

    return answer, 150  # Mock token count


# ---------------------------------------------------------------------------
# Real answer generation (EC2 with LLaMA)
# ---------------------------------------------------------------------------
def _real_generate_answer(
    question: str,
    chunks: list[dict[str, Any]],
) -> tuple[str, int]:
    """
    Generate a real answer using the fine-tuned LLaMA model.

    Only runs on EC2 where USE_REAL_LLAMA=true and torch is available.
    Returns (answer_text, tokens_used).
    """
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel

        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            page = chunk.get("page_number", "?")
            text = chunk.get("text", "")
            context_parts.append(f"[Excerpt {i}, Page {page}]:\n{text}")

        context = "\n\n".join(context_parts)
        prompt = GENERATION_CONTEXT_TEMPLATE.format(
            context=context, question=question
        )

        # Load base model in 4-bit
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        base_model_id = "NousResearch/Meta-Llama-3.1-8B-Instruct"
        tokenizer = AutoTokenizer.from_pretrained(base_model_id)
        model = AutoModelForCausalLM.from_pretrained(
            base_model_id, quantization_config=bnb_config, device_map="auto"
        )

        # Load QLoRA adapter
        adapter_path = "models/llama-finance-adapter"
        model = PeftModel.from_pretrained(model, adapter_path)
        model.eval()

        # Format as chat message
        messages = [
            {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        input_text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
        input_len = inputs["input_ids"].shape[1]

        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=500,
                temperature=0.3,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )

        # Decode only the new tokens
        answer = tokenizer.decode(
            outputs[0][input_len:], skip_special_tokens=True
        ).strip()

        total_tokens = outputs[0].shape[0]
        logger.info(f"LLaMA generated answer: {len(answer)} chars, {total_tokens} tokens")

        return answer, total_tokens

    except Exception as e:
        logger.error(f"Real LLaMA generation failed: {e}. Falling back to mock.")
        return _mock_generate_answer(question, chunks)


# ---------------------------------------------------------------------------
# Public function — called by the RAG service
# ---------------------------------------------------------------------------
def generate_answer(
    question: str,
    chunks: list[dict[str, Any]],
) -> tuple[str, int]:
    """
    Generate a grounded answer from retrieved chunks.

    Args:
        question: the original user question
        chunks: top-k re-ranked chunks (each has 'text', 'page_number', etc.)

    Returns:
        tuple of (answer_text, tokens_used)
    """
    logger.info(f"Generating answer from {len(chunks)} chunks...")

    if settings.USE_REAL_LLAMA:
        return _real_generate_answer(question, chunks)
    else:
        return _mock_generate_answer(question, chunks)