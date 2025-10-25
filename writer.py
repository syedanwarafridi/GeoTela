from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import re
from utils import tavily_search

# ============================================================
# 1️⃣ Function: Load Qwen Model (with error handling)
# ============================================================
def load_qwen_model(model_name: str = "Qwen/Qwen3-0.6B"):
    """
    Loads the Qwen model and tokenizer once for reuse.
    Returns (model, tokenizer) or raises RuntimeError if failed.
    """
    try:
        print(f"🔄 Loading model: {model_name} ...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto"
        )
        print("✅ Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise RuntimeError(f"Model loading failed: {e}")


# ============================================================
# 2️⃣ Function: Write History (with error handling)
# ============================================================
def write_history(model, tokenizer, location: str) -> dict:

    query=f"Interesting History of {location}"
    context = tavily_search(query=query, max_results=2)
    try:
        prompt = (
            "<|im_start|>system\n"
            "You are a historian / assistant. You will produce exactly one paragraph. "
            "You must use only the information in the CONTEXT below and must not add any external knowledge.\n\n"
            f"CONTEXT:\n{context}\n\n"
            "WRITING INSTRUCTIONS:\n"
            f"- Write a concise history of {location} in one paragraph.\n"
            "- Use ONLY the given context.\n"
            "- Do NOT invent or assume any details.\n"
            "- Output ONLY the paragraph, no extra commentary.\n"
            "<|im_end|>\n"
            "<|im_start|>user\n"
            "Answer:\n"
            "<|im_end|>\n"
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        generated_ids = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.1,
            top_p=0.9
        )

        generated_text = tokenizer.decode(
            generated_ids[0][inputs["input_ids"].shape[-1]:],
            skip_special_tokens=True
        ).strip()

        if not generated_text:
            return {"error": "No history generated."}

        return {"history": generated_text}

    except torch.cuda.OutOfMemoryError:
        return {"error": "GPU out of memory during text generation."}
    except Exception as e:
        return {"error": f"History generation failed: {str(e)}"}


# ============================================================
# 3️⃣ Function: Extract Historical Places (with error handling)
# ============================================================
def extract_historical_places(model, tokenizer, location: str) -> dict:
    if not location:
        return {"error": "Location is required."}

    try:
        query = f"Historical places near to {location} for visit"
        try:
            context = tavily_search(query=query, max_results=2)
            if not context or "results" not in context:
                return {"error": "No context retrieved from Tavily."}
        except Exception as e:
            return {"error": f"Tavily search failed: {str(e)}"}

        text = "\n".join([i.get("content", "") for i in context.get("results", [])])
        if not text.strip():
            return {"error": "No valid content found in Tavily results."}

        # 🧠 Build prompt
        prompt = f"""<|im_start|>system
        You are a precise information extraction assistant.
        Your task is to extract location names mentioned in the text.
        Follow these rules strictly:
        - Only include complete location names (e.g., "Palace of Versailles", not "Palace of").
        - Do not include partial, cut-off, or single generic words like "Palace", "Temple", or "Mount".
        - Each location must be a proper noun (historical or geographical name).
        - Return results ONLY as a valid JSON list of strings, with no explanation or extra text.
        {{"locations": ["Location1", "Location2", "Location3"]}}

        If no valid location names are found, return {{"locations": []}}.
        <|im_end|>
        <|im_start|>user
        Extract all complete location names mentioned in the text below.

        TEXT:
        {text}

        OUTPUT:
        <|im_end|>"""

        # 🔹 Generate
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.2,
            top_p=0.9,
            do_sample=False
        )

        generated_text = tokenizer.decode(
            generated_ids[0][inputs["input_ids"].shape[-1]:],
            skip_special_tokens=True
        ).strip()

        if not generated_text:
            return {"error": "Model did not return any output."}

        # 🔹 Extract JSON block safely
        matches = re.findall(r'\{[\s\S]*?\}', generated_text)
        if matches:
            json_str = matches[-1]
            try:
                extracted_output = json.loads(json_str)
            except json.JSONDecodeError:
                cleaned = json_str.replace("'", '"').replace("\n", "").strip()
                extracted_output = json.loads(cleaned)
        else:
            extracted_output = {"locations": []}

        if not isinstance(extracted_output, dict) or "locations" not in extracted_output:
            extracted_output = {"locations": []}

        return extracted_output

    except torch.cuda.OutOfMemoryError:
        return {"error": "GPU out of memory during extraction."}
    except Exception as e:
        return {"error": f"Place extraction failed: {str(e)}"}

if __name__ == "__main__":
    try:
        model, tokenizer = load_qwen_model()


        history_result = write_history(model, tokenizer, "Paris")
        print("🕰️ History Result:", json.dumps(history_result, indent=2))

        # # Example 2: Extract historical places
        # places_result = extract_historical_places(model, tokenizer, "Paris")
        # print("📍 Historical Places:", json.dumps(places_result, indent=2))

    except RuntimeError as re:
        print(f"⚠️ Critical error: {re}")
    except Exception as e:
        print(f"⚠️ Unexpected failure: {e}")
