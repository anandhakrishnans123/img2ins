import os
import pandas as pd
from io import BytesIO
from google import genai
import re
import json
from pymongo import MongoClient

def get_mongo_client():
    """Get MongoDB client using environment variables."""
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("Missing MONGODB_URI environment variable")
    return MongoClient(uri)

# Initialize default client and collections
client = get_mongo_client()
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
"""