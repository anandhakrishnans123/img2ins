import requests
import json
import pandas as pd
from pymongo import MongoClient

# =====================================================
# CONFIGURATION
# =====================================================

GRAPHQL_URL = "https://42fd29e5b225.ngrok-free.app/graphql"  # Replace with your actual endpoint
MONGO_URI = "mongodb+srv://myUser:yH89cVer8fkdshDQ@cluster0.ly5onxl.mongodb.net/?appName=Cluster0"

# =====================================================
# FUNCTION DEFINITION
# =====================================================

def process_s_id(s_id: str):
    """
    Given an s_id, fetch corresponding MongoDB record,
    match it with GraphQL call data, and export both
    to a structured Excel file.

    Args:
        s_id (str): The unique identifier to process.
    """
    print(f"\n🚀 Processing s_id: {s_id}")

    # --- Step 1: Connect to MongoDB ---
    client = MongoClient(MONGO_URI)
    db = client["audio_processing"]
    collection = db["audio_results"]

    # Fetch the Mongo document for given s_id
    mongo_doc = collection.find_one({"s_id": s_id})
    if not mongo_doc:
        print(f"❌ No document found in MongoDB for s_id: {s_id}")
        return None

    # --- Step 2: Run GraphQL Query ---
    query = """
    query GetEntityByHid {
        getCallDataTranscribe(
            fromDate: "2025-10-01T18:30:00.000Z"
            toDate: "2025-10-30T17:59:59.000Z"
        ) {
            s3Uploaded
            entityId
            callId
            entityName
            state
            phone
            city
            country
            status
            description
            securityDeposit
            minRent
            maxRent
            ownerName
            email
            startedYear
            fullTimeWarden
            visitorsAllowed
            website
            entityType
            totalBeds
            Recordings {
                s3Url
                dateCreatedInUpdates
            }
        }
    }
    """

    try:
        response = requests.post(GRAPHQL_URL, json={"query": query})
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ GraphQL query failed: {e}")
        return None

    entities = data.get("data", {}).get("getCallDataTranscribe", [])
    if not entities:
        print("❌ No data returned from GraphQL")
        return None

    graphql_df = pd.DataFrame(entities)

    # --- Step 3: Match Mongo s_id with GraphQL callId ---
    match_row = graphql_df[graphql_df["callId"] == s_id]
    if match_row.empty:
        print(f"❌ No matching callId found in GraphQL for s_id: {s_id}")
        return None

    print(f"✅ Match found for s_id: {s_id}")

    # --- Step 4: Extract and flatten details ---
    entity_row = match_row.iloc[0].to_dict()
    recordings = entity_row.get("Recordings", [])
    if isinstance(recordings, list) and recordings:
        entity_row["recordings_count"] = len(recordings)
        entity_row["first_recording_url"] = recordings[0].get("s3Url")
        entity_row["first_recording_date"] = recordings[0].get("dateCreatedInUpdates")
    entity_row.pop("Recordings", None)

    # --- Step 5: Prepare Excel sheets ---
    mongo_summary = pd.DataFrame([{"s_id": s_id, "source": "A", "_id": str(mongo_doc.get("_id"))}])
    entity_info_df = pd.DataFrame([entity_row])
    final_df = pd.concat([mongo_summary, entity_info_df], axis=1)

    mongo_full_df = pd.DataFrame([mongo_doc])
    mongo_full_df = mongo_full_df.applymap(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)

    # --- Step 6: Save to Excel ---
    output_path = f"combined.xlsx"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        final_df.to_excel(writer, sheet_name="Matched_Entity_Info", index=False)
        mongo_full_df.to_excel(writer, sheet_name="MongoDB_Full_Document", index=False)

    print(f"📁 Excel saved successfully → {output_path}")
    return output_path