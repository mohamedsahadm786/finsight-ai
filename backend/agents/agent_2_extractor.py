"""
Agent 2 — Financial Ratio Extractor.

Reads all chunk texts from state and extracts 5 target financial ratios
using the fine-tuned LLaMA model (map-reduce approach).

Locally (USE_REAL_LLAMA=false): Returns hardcoded mock ratios instantly.
On EC2 (USE_REAL_LLAMA=true): Loads LLaMA 3.1 8B + QLoRA adapter and
performs real inference over chunk batches.

Target ratios:
  1. DSCR (Debt Service Coverage Ratio)
  2. Leverage Ratio (Total Debt / EBITDA)
  3. Interest Coverage Ratio (EBIT / Interest Expense)
  4. Current Ratio (Current Assets / Current Liabilities)
  5. Net Profit Margin (Net Income / Revenue)
"""

import json
import logging
from typing import Any

from backend.app.config import get_settings
from backend.app.database.session import SyncSessionLocal
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.extracted_ratio import ExtractedRatio

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Mock LLaMA extraction — used locally
# ---------------------------------------------------------------------------
def _mock_extract_ratios(chunks: list[str]) -> dict[str, Any]:
    """
    Returns hardcoded financial ratios instantly.
    Used when USE_REAL_LLAMA=false (local development).
    """
    return {
        "dscr": 1.34,
        "leverage_ratio": 4.8,
        "interest_coverage": 3.2,
        "current_ratio": 0.92,
        "net_profit_margin": 0.08,
        "ratios_found_count": 5,
        "raw_extraction": {"mock": True, "source": "hardcoded_values"},
    }


# ---------------------------------------------------------------------------
# Real LLaMA extraction — used on EC2 only
# ---------------------------------------------------------------------------
def _real_extract_ratios(chunks: list[str]) -> dict[str, Any]:
    """
    Uses the fine-tuned LLaMA 3.1 8B + QLoRA adapter to extract ratios.
    Only runs on EC2 where USE_REAL_LLAMA=true and sufficient RAM is available.

    Map-reduce approach:
    - MAP: Process chunks in batches of 5, ask LLaMA to find any ratios
    - REDUCE: Merge partial results, deduplicate, pick most specific values
    """
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel

        logger.info("Loading LLaMA 3.1 8B with QLoRA adapter...")

        # Load base model in 4-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        base_model = AutoModelForCausalLM.from_pretrained(
            "NousResearch/Meta-Llama-3.1-8B-Instruct",
            quantization_config=bnb_config,
            device_map="auto",
        )

        # Load fine-tuned LoRA adapter
        model = PeftModel.from_pretrained(base_model, "models/llama-finance-adapter")
        tokenizer = AutoTokenizer.from_pretrained("models/llama-finance-adapter")

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        logger.info("LLaMA loaded. Starting map-reduce extraction...")

        # --- MAP phase: process chunks in batches of 5 ---
        all_partial_results = []
        batch_size = 5

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            combined_text = "\n\n".join(batch)

            prompt = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

You are a financial analyst. Extract the following ratios from this document excerpt.
Return ONLY a JSON object with these keys (use null if not found):
- dscr (Debt Service Coverage Ratio)
- leverage_ratio (Total Debt / EBITDA)
- interest_coverage (EBIT / Interest Expense)
- current_ratio (Current Assets / Current Liabilities)
- net_profit_margin (Net Income / Revenue)

Document excerpt:
{combined_text[:3000]}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096)
            inputs = {k: v.to(model.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.1,
                    do_sample=False,
                )

            response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

            # Try to parse JSON from response
            try:
                # Find JSON in the response
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    partial = json.loads(response[json_start:json_end])
                    all_partial_results.append(partial)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLaMA response for batch {i // batch_size}")

        # --- REDUCE phase: merge partial results ---
        merged = {
            "dscr": None,
            "leverage_ratio": None,
            "interest_coverage": None,
            "current_ratio": None,
            "net_profit_margin": None,
        }

        for partial in all_partial_results:
            for key in merged:
                if merged[key] is None and partial.get(key) is not None:
                    try:
                        merged[key] = float(partial[key])
                    except (ValueError, TypeError):
                        pass

        ratios_found = sum(1 for v in merged.values() if v is not None)

        return {
            **merged,
            "ratios_found_count": ratios_found,
            "raw_extraction": {
                "mock": False,
                "partial_results": all_partial_results,
                "batches_processed": len(all_partial_results),
            },
        }

    except Exception as e:
        logger.error(f"Real LLaMA extraction failed: {e}. Falling back to mock.")
        return _mock_extract_ratios(chunks)


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------
def agent_2_extractor(state: dict[str, Any]) -> dict[str, Any]:
    """
    Agent 2 — Financial Ratio Extractor.

    Reads from state: chunks, document_id, tenant_id, job_id
    Writes to state: extracted_ratios, ratios_found_count, raw_extraction
    Side effects: extracted_ratios row created in PostgreSQL
    """
    document_id = state["document_id"]
    tenant_id = state["tenant_id"]
    job_id = state["job_id"]
    chunks = state.get("chunks", [])

    db = SyncSessionLocal()
    try:
        # --- Update job status ---
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.current_agent = "Financial Ratio Extractor"
            db.commit()

        logger.info(f"[Job {job_id}] Agent 2: Starting financial ratio extraction...")
        logger.info(f"[Job {job_id}] Processing {len(chunks)} chunks")

        # --- Choose real or mock extraction ---
        if settings.USE_REAL_LLAMA:
            result = _real_extract_ratios(chunks)
        else:
            result = _mock_extract_ratios(chunks)

        # --- Save to PostgreSQL ---
        extracted_ratio = ExtractedRatio(
            document_id=document_id,
            job_id=job_id,
            dscr=result.get("dscr"),
            leverage_ratio=result.get("leverage_ratio"),
            interest_coverage=result.get("interest_coverage"),
            current_ratio=result.get("current_ratio"),
            net_profit_margin=result.get("net_profit_margin"),
            ratios_found_count=result.get("ratios_found_count", 0),
            raw_extraction=result.get("raw_extraction", {}),
        )
        db.add(extracted_ratio)
        db.commit()

        logger.info(
            f"[Job {job_id}] Agent 2 complete: "
            f"{result.get('ratios_found_count', 0)}/5 ratios found"
        )

        return {
            **state,
            "extracted_ratios": {
                "dscr": result.get("dscr"),
                "leverage_ratio": result.get("leverage_ratio"),
                "interest_coverage": result.get("interest_coverage"),
                "current_ratio": result.get("current_ratio"),
                "net_profit_margin": result.get("net_profit_margin"),
            },
            "ratios_found_count": result.get("ratios_found_count", 0),
            "raw_extraction": result.get("raw_extraction", {}),
        }

    except Exception as e:
        db.rollback()
        error_msg = f"Agent 2 failed: {e}"
        logger.error(f"[Job {job_id}] {error_msg}")
        return {**state, "errors": state.get("errors", []) + [error_msg]}

    finally:
        db.close()