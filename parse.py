import os
import pandas as pd
import ast
import json
from io import BytesIO
from google import genai

def parse_text_to_json(text: str):
    """
    Parses a given text into structured JSON format using Gemini model
    and returns only the specified fields as a Python dict. This function no
    longer writes files to disk — it returns the parsed dict so callers can
    decide how to persist or download it.

    Args:
        text (str): The input unstructured text to parse.

    Returns:
        dict: Parsed JSON output with only the requested fields.
    """
    # Fields we want in the output
    fields = [
        "Room Type",
        "Cost",
        "Desired Location",
        "Available Location",
        "Status of Inhabitant",
        "Required Amenities",
        "Alternative Suggestions",
        "RoomDetails.requested_type",
        "RoomDetails.requested_bathroom_type"
    ]

    # Construct prompt
    prompt = f"""
    Parse the following text into JSON containing ONLY these fields: {fields}.
    For any field that is missing, return null.
    Ensure nested fields like 'RoomDetails.requested_type' and 'RoomDetails.requested_bathroom_type'
    are structured under a 'RoomDetails' object. The JSON should be valid and directly usable.
    Text to parse:
    {text}
    """

    # Get API key
    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GENI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing API key. Set GENAI_API_KEY or GEMINI_API_KEY environment variable.")

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    MODEL_NAME = "gemini-2.5-flash"

    # Call Gemini
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt]
    )

    # Clean model output
    clean_text = response.text.strip().strip("```")
    if clean_text.lower().startswith("json"):
        clean_text = clean_text[4:].strip()

    # Convert to dict
    try:
        parsed_json = json.loads(clean_text)
        return parsed_json
    except Exception:
        try:
            return ast.literal_eval(clean_text)
        except Exception:
            return {"error": "Failed to parse JSON", "raw_text": clean_text}


def json_to_excel_bytes(json_data: dict) -> BytesIO:
    """
    Convert a JSON/dict to an in-memory Excel file and return a BytesIO buffer.
    """
    output = BytesIO()
    df = pd.json_normalize(json_data, sep='.')
    # Use openpyxl engine via pandas
    df.to_excel(output, index=False)
    output.seek(0)
    return output


def json_to_excel(json_data: dict, output_file: str = "parsed_data.xlsx"):
    """
    Converts a JSON dictionary to an Excel file, keeping only the requested fields.
    
    Args:
        json_data (dict): Parsed JSON data.
        output_file (str): Filename for the Excel output.
    
    Returns:
        str: Path to the saved Excel file.
    """
    # Flatten JSON
    df = pd.json_normalize(json_data, sep='.')

    # Save to Excel
    df.to_excel(output_file, index=False)
    return output_file


# -------------------- Example usage --------------------
if __name__ == "__main__":
    sample_text = """
    Room Type:
    Initially requested: Single room (with private bathroom).
    Currently available: Two-sharing room, which can be taken as a single.
    Cost:
    9500 (for the two-sharing room, even if taken as a single).
    Location:
    Desired location by tenant: Palayam.
    Available locations for the mentioned room type: Nandavanam, Murinjapalam.
    Status of Inhabitant:
    Not specified (no explicit mention of student or working professional, nor any associated institution/company).
    Required Amenities:
    Initially inquired about a private bathroom for a single room. The currently available two-sharing room comes with a shared bathroom.
    Alternative Suggestions:
    Other hostel locations mentioned by Speaker 1: Nandavanam, Nanthankode, Murinjapalam.
    """

    # Step 1: Parse text to JSON
    parsed_json = parse_text_to_json(sample_text)

    # Step 2: Convert JSON to Excel
    excel_file = json_to_excel(parsed_json, output_file="parsed_data.xlsx")
    print(f"✅ Excel file saved as: {excel_file}")
