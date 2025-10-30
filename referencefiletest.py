import requests
import json
import pandas as pd
from pymongo import MongoClient

# =====================================================
# CONFIGURATION
# =====================================================

GRAPHQL_URL = "https://42fd29e5b225.ngrok-free.app/graphql"  # Replace with your endpoint
MONGO_URI = "mongodb+srv://myUser:yH89cVer8fkdshDQ@cluster0.ly5onxl.mongodb.net/?appName=Cluster0"

# =====================================================
# FUNCTION DEFINITION
# =====================================================

def match_sids_to_graphql(s_ids=None, from_date="2025-10-01T18:30:00.000Z", to_date="2025-10-30T17:59:59.000Z"):
    """
    Match one or more Mongo s_ids with GraphQL callId data and export to Excel.
    
    Args:
        s_ids (list | str | None): 
            - List of s_ids to match
            - Single s_id string
            - "latest" or None to auto-fetch the latest from MongoDB
        from_date (str): Start ISO datetime for GraphQL query
        to_date (str): End ISO datetime for GraphQL query
    """

    # -------------------------------------
    # Connect MongoDB
    # -------------------------------------
    client = MongoClient(MONGO_URI)
    db = client["audio_processing"]
    collection = db["audio_results"]

    # Auto-fetch latest if not given
    if s_ids in [None, "latest"]:
        latest_doc = collection.find_one(sort=[("_id", -1)])
        if not latest_doc:
            raise Exception("❌ No document found in MongoDB.")
        s_ids = [latest_doc.get("s_id")]
        print(f"📘 Auto-fetched latest s_id: {s_ids[0]}")
    elif isinstance(s_ids, str):
        s_ids = [s_ids]  # ensure list

    # -------------------------------------
    # GraphQL Query
    # -------------------------------------
    query = f"""
    query GetEntityByHid {{
        getCallDataTranscribe(
            fromDate: "{from_date}"
            toDate: "{to_date}"
        ) {{
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
            Recordings {{
                s3Url
                dateCreatedInUpdates
            }}
        }}
    }}
    """

    response = requests.post(GRAPHQL_URL, json={"query": query})
    if response.status_code != 200:
        raise Exception(f"❌ GraphQL query failed! ({response.status_code}) → {response.text}")

    data = response.json()
    entities = data.get("data", {}).get("getCallDataTranscribe", [])
    if not entities:
        raise Exception("❌ No results found from GraphQL query.")
    graphql_df = pd.DataFrame(entities)

    # -------------------------------------
    # Match Each s_id
    # -------------------------------------
    all_results = []
    mongo_docs = []

    for sid in s_ids:
        match_row = graphql_df[graphql_df["callId"] == sid]

        if match_row.empty:
            print(f"❌ No matching callId found for s_id: {sid}")
            continue

        print(f"✅ Matching callId found for s_id: {sid}")

        entity_row = match_row.iloc[0].to_dict()
        recordings = entity_row.get("Recordings", [])
        if isinstance(recordings, list) and recordings:
            entity_row["recordings_count"] = len(recordings)
            entity_row["first_recording_url"] = recordings[0].get("s3Url")
            entity_row["first_recording_date"] = recordings[0].get("dateCreatedInUpdates")
        entity_row.pop("Recordings", None)

        mongo_doc = collection.find_one({"s_id": sid})
        mongo_docs.append(mongo_doc)

        mongo_summary = {
            "_id": str(mongo_doc.get("_id")) if mongo_doc else None,
            "source": "A",
            "s_id": sid,
        }

        all_results.append({**mongo_summary, **entity_row})

    if not all_results:
        print("⚠️ No matches found for any given s_id(s).")
        return None

    # -------------------------------------
    # Convert to DataFrames
    # -------------------------------------
    matched_df = pd.DataFrame(all_results)
    mongo_full_df = pd.DataFrame(mongo_docs).applymap(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)

    # -------------------------------------
    # Save Excel Output
    # -------------------------------------
    output_path = "matched_calls_from_graphql.xlsx"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        matched_df.to_excel(writer, sheet_name="Matched_Entities", index=False)
        mongo_full_df.to_excel(writer, sheet_name="MongoDB_Full_Docs", index=False)

    print(f"\n✅ Excel saved successfully → {output_path}")
    print("📄 Sheets:")
    print("  - Matched_Entities")
    print("  - MongoDB_Full_Docs")

    return output_path

# =====================================================
# Example Usage
# =====================================================
if __name__ == "__main__":
    # Option 1: Auto-fetch latest Mongo s_id
    match_sids_to_graphql("latest")

    # Option 2: Manually pass one or more s_ids
    # match_sids_to_graphql(["S1234", "S5678"])
