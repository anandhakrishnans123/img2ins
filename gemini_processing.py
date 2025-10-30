import os
import pandas as pd
from io import BytesIO
from google import genai
from parse import parse_text_to_json, json_to_excel_bytes
from pymongo import MongoClient

# ---------------------------------------------
# Configuration
# ---------------------------------------------
MODEL_NAME = "gemini-2.5-flash"

# --- Prompts ---
TRANSCRIPTION_PROMPT = (
    "Transcribe the provided audio file accurately with timestamps. "
    "For each spoken segment, include the start time in [MM:SS] format at the beginning of the line. "
    "Example format:\n"
    "[00:00] Speaker: Hello, welcome to the meeting\n"
    "[00:05] Speaker: Today we'll discuss...\n"
    "Ensure accurate timing and capture all spoken words, including speaker changes if identifiable."
)

SUMMARY_PROMPT = SUMMARY_PROMPT = (
    """Extract the following information from the provided conversation text:
    1. **Room Type**: Identify and extract the type of room being discussed (e.g., single, double, shared).
    2. **Cost**: Determine the cost associated with the room or accommodation mentioned.
    3. **Location**: Extract the geographical location of the accommodation.
    4. **Status of Inhabitant**: Specify whether the tenant is a student or a working professional, and if applicable, include the name of the company or institution they are associated with.
    5. **Required Amenities**: List any specific amenities that the tenant requires or is looking for in the accommodation (e.g., Wi-Fi, laundry, kitchen access).
    6. **Alternative Suggestions**: Note any other hostel or accommodation options suggested to the tenant by the landlord during the conversation.
    7. **Short Summary**: Provide a concise summary (2–3 sentences) describing the overall context and main points of the conversation.
    8. **Key Takeaways**: Highlight the most important insights or decisions from the conversation in bullet points.
    Ensure that the extraction is accurate, structured, and concise, providing clear labels for each piece of information collected."""
)


# ---------------------------------------------
# MongoDB Setup
# ---------------------------------------------
def get_mongo_client():
    """
    Create a MongoDB client using environment variables or default localhost.
    """
    mongo_uri = (
        os.getenv("MONGODB_URI")
        or os.getenv("MONGO_URI")
        or "mongodb://localhost:27017/"
    )
    return MongoClient(mongo_uri)

def save_to_mongo(s_id, transcription, summary, insights):
    """
    Save processed data to MongoDB.
    """
    try:
        client = get_mongo_client()
        db = client["audio_processing"]
        collection = db["audio_results"]

        document = {
            "s_id": s_id,  # ✅ Added s_id
            "transcription": transcription,
            "summary": summary,
            "insights": insights
        }

        inserted_id = collection.insert_one(document).inserted_id
        print(f"✅ Data saved to MongoDB (Document ID: {inserted_id}) with s_id: {s_id}")
        client.close()
    except Exception as e:
        print(f"❌ Failed to save to MongoDB: {e}")

# ---------------------------------------------
# Core Function
# ---------------------------------------------
def process_audio_file(audio_path: str, s_id: str = None, api_key: str = None) -> dict:
    """
    Process an audio file to generate transcription, structured summary, Excel, and store in MongoDB.

    Args:
        audio_path (str): Path to the local audio file (.mp3, .wav, .m4a).
        s_id (str, optional): Call identifier (SID).
        api_key (str, optional): Gemini API key.

    Returns:
        dict: {
            "transcription": str,
            "summary": str,
            "excel_bytes": BytesIO
        }
    """
    # --------------------------
    # API Setup
    # --------------------------
    api_key = (
        api_key
        or os.getenv("GENAI_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("API_KEY")
    )

    if not api_key:
        raise ValueError("❌ Gemini API key not found. Please set it in environment variables or pass it explicitly.")

    client = genai.Client(api_key=api_key)

    # --------------------------
    # Step 1: Upload Audio
    # --------------------------
    try:
        audio_file = client.files.upload(file=audio_path)
    except Exception as e:
        raise RuntimeError(f"Audio upload failed: {e}")

    # --------------------------
    # Step 2: Transcription
    # --------------------------
    try:
        transcription_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[TRANSCRIPTION_PROMPT, audio_file]
        )
        transcription = transcription_response.text
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")

    # --------------------------
    # Step 3: Summarization
    # --------------------------
    try:
        summary_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[SUMMARY_PROMPT, transcription]
        )
        summary = summary_response.text
    except Exception as e:
        raise RuntimeError(f"Summary generation failed: {e}")

    # --------------------------
    # Step 4: Parse Summary → JSON → Excel
    # --------------------------
    try:
        parsed_json = parse_text_to_json(summary)
        if isinstance(parsed_json, dict) and parsed_json.get("error"):
            raise ValueError(f"Parsing failed: {parsed_json.get('error')}")
        excel_bytes = json_to_excel_bytes(parsed_json)
    except Exception as e:
        raise RuntimeError(f"Excel generation failed: {e}")

    # --------------------------
    # Step 5: Save to MongoDB
    # --------------------------
    try:
        save_to_mongo(s_id, transcription, summary, parsed_json)
    except Exception as e:
        print(f"❌ MongoDB save error: {e}")

    # --------------------------
    # Step 6: Cleanup
    # --------------------------
    try:
        client.files.delete(name=audio_file.name)
    except Exception:
        pass

    # --------------------------
    # Step 7: Return results
    # --------------------------
    return {
        "transcription": transcription,
        "summary": summary,
        "excel_bytes": excel_bytes
    }

# ---------------------------------------------
# Example usage
# ---------------------------------------------
if __name__ == "__main__":
    audio_path = "audio.wav"  # Replace with your actual file
    s_id = "18281b98135a5519cf11f751d16c19ar"  # ✅ Example SID
    result = process_audio_file(audio_path, s_id=s_id)

    print("\n--- Transcription ---\n")
    print(result["transcription"][:1000], "...\n")

    print("\n--- Summary ---\n")
    print(result["summary"])

    # Save Excel file with s_id in the filename if available
    excel_filename = f"audio_insights_{s_id}.xlsx" if s_id else "audio_insights.xlsx"
    with open(excel_filename, "wb") as f:
        f.write(result["excel_bytes"].getvalue())
    print(f"\n✅ Excel file saved as {excel_filename}")
