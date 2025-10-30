import os
import pandas as pd
from io import BytesIO
from google import genai
import re
import json
from pymongo import MongoClient
uri = "mongodb+srv://myUser:yH89cVer8fkdshDQ@cluster0.ly5onxl.mongodb.net/?appName=Cluster0"
client = MongoClient(uri)
db = client["audio_processing"]
collection = db["audio_results"]
# ---------------------------------------------
# Configuration
# ---------------------------------------------
MODEL_NAME = "gemini-2.5-flash"
COMPARE_PROMPT = """
You are an AI comparison model.

You will be given two datasets:
- Dataset A: Website Hostel Info
- Dataset B: Transcribed Call Info

Goal: Compare them and output **only valid JSON (no extra text)**.

Do not predict or invent values.  
If data cannot be confidently determined, set it to null.

---

### OUTPUT FORMAT (Must follow exactly)

{
  "general_comparison": {
    "price_comparison": {
      "website_hostel_info": {"price": <number or null>},
      "transcribed_call_info": {"price": <number or null>},
      "difference": <number or null>
    },
    "place_match": {
      "website_hostel_info": {"place": "<string or null>"},
      "transcribed_call_info": {"place": "<string or null>"}
    },
    "room_type": {
      "website_hostel_info": {"type": "<string or null>"},
      "transcribed_call_info": {"type": "<string or null>"}
    },
    "amenities": {
      "website_hostel_info": ["<string>", ...],
      "transcribed_call_info": ["<string>", ...]
    },
    "contact_number": {
      "website_hostel_info": ["<digits>"],
      "transcribed_call_info": ["<digits>"]
    },
    "address": {
      "website_hostel_info": "<string or null>",
      "transcribed_call_info": "<string or null>"
    },
    "gender_allowed": {
      "website_hostel_info": ["male","female","coed","other"],
      "transcribed_call_info": ["male","female","coed","other"]
    },
    "availability": {
      "website_hostel_info": "<string or null>",
      "transcribed_call_info": "<string or null>"
    },
    "deposit_amount": {
      "website_hostel_info": <number or null>,
      "transcribed_call_info": <number or null>
    },
    "meal_included": {
      "website_hostel_info": "<yes/no/null>",
      "transcribed_call_info": "<yes/no/null>"
    }
  },

  "summary": {
    "overview": "<brief human summary of main similarities and differences>",
    "key_takeaways": ["<short bullet insights>"]
  },

  "action_points": [
    "<concise steps to reduce mismatch or improve consistency>"
  ],

  "match_score": <0–100>,

  "metadata": {
    "comparison_run_id": "<uuid or null>",
    "generated_at": "<ISO8601 timestamp>",
    "notes": "<optional notes or null>"
  }
}

---

### RULES
- Always return valid JSON only.
- Normalize all text (lowercase, trimmed).
- Compare prices and deposits numerically.
- Use fuzzy matching for textual fields (name, address, etc.).
- Be concise — no explanation outside the JSON.
"""





# ---------------------------------------------
# Core Comparison Function
# ---------------------------------------------
def compare_excel_sheets(file_path: str, api_key: str = None) -> dict:
    """
    Compare Sheet1 (Website Info) and Sheet2 (Call Transcription Info) using Gemini 2.5 Flash.

    Args:
        file_path (str): Path to Excel file containing two sheets.
        api_key (str, optional): Gemini API key.
    Returns:
        dict: Comparison results with structured Gemini output.
    """

    # --- API Setup ---
    api_key = (
        api_key
        or os.getenv("GENAI_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("API_KEY")
    )
    if not api_key:
        raise ValueError("❌ Gemini API key not found. Please set it in environment variables or pass explicitly.")

    client = genai.Client(api_key=api_key)

    # --- Read Excel Sheets ---
    df_a = pd.read_excel(file_path, sheet_name=0)  # Sheet1 → A
    df_b = pd.read_excel(file_path, sheet_name=1)  # Sheet2 → B

    # Convert to JSON for better contextual understanding
    json_a = df_a.to_dict(orient="records")
    json_b = df_b.to_dict(orient="records")

    # --- Construct Gemini Prompt ---
    prompt = f"""
{COMPARE_PROMPT}

Dataset A (Website Info):
{json_a}

Dataset B (Transcribed Call Info):
{json_b}
"""

    # --- Send to Gemini ---
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt]
        )
        comparison_output = response.text
    except Exception as e:
        raise RuntimeError(f"Gemini comparison failed: {e}")

    # --- Return structured output ---
    return {
        "comparison_result": comparison_output
    }
    
def mongo_insert(file_path:str):
    result = compare_excel_sheets(file_path)

    print("\n--- Gemini Comparison Result ---\n")
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", result["comparison_result"].strip())
    print(cleaned)
    raw_text = result["comparison_result"]

    # Remove ```json or ``` from start/end
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip())
    # --- Step 2: Parse JSON safely ---
    print(cleaned)
    try:
        parsed_json = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("❌ Invalid JSON:", e)
        parsed_json = None

    # --- Step 3: Insert into MongoDB ---
    if parsed_json:
        uri = "mongodb+srv://myUser:yH89cVer8fkdshDQ@cluster0.ly5onxl.mongodb.net/?appName=Cluster0"
        client = MongoClient(uri)
        db = client["data_processing"]
        collection = db["comparison_results"]

        result = collection.insert_one(parsed_json)
        print("✅ Inserted document with ID:", result.inserted_id)

# ---------------------------------------------
# Example Usage
# ---------------------------------------------
if __name__ == "__main__":
    excel_path = r"matched_call_entity_from_graphql.xlsx"

    print("🔍 Comparing Website Info (Sheet1) and Call Info (Sheet2) using Gemini 2.5 Flash...\n")
    result = compare_excel_sheets(excel_path)

    print("\n--- Gemini Comparison Result ---\n")
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", result["comparison_result"].strip())
    print(cleaned)
    raw_text = result["comparison_result"]

    # Remove ```json or ``` from start/end
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip())
    # --- Step 2: Parse JSON safely ---
    print(cleaned)
    try:
        parsed_json = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("❌ Invalid JSON:", e)
        parsed_json = None

    # --- Step 3: Insert into MongoDB ---
    if parsed_json:
        uri = "mongodb+srv://myUser:yH89cVer8fkdshDQ@cluster0.ly5onxl.mongodb.net/?appName=Cluster0"
        client = MongoClient(uri)
        db = client["data_processing"]
        collection = db["comparison_results"]

        result = collection.insert_one(parsed_json)
        print("✅ Inserted document with ID:", result.inserted_id)

    
