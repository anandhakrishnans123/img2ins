import requests
import json
from datetime import datetime

# Automatically get today's date in MM/DD/YYYY format
Specific_date = datetime.now().strftime("%m/%d/%Y")

def fetch_call_data_transcribe(
    url: str = "https://42fd29e5b225.ngrok-free.app/graphql",
    from_date: str =Specific_date,
    to_date: str = Specific_date,
    limit: int = 10
):
    """
    Fetch call transcription data from GraphQL endpoint within a given date range.

    Args:
        url (str): GraphQL endpoint URL.
        from_date (str): Start date in ISO 8601 format.
        to_date (str): End date in ISO 8601 format.
        limit (int): Limit number of records to return.

    Returns:
        list: List of call transcription data dictionaries (limited by `limit`).
    """

    # --- GraphQL query ---
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

    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json={"query": query}, headers=headers)

        if response.status_code == 200:
            data = response.json()
            call_data = data.get("data", {}).get("getCallDataTranscribe", [])
            return call_data[:limit]
        else:
            print(f"❌ Failed! Status code: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"⚠️ Error occurred: {e}")
        return []

# --- Example Usage ---
if __name__ == "__main__":
    endpoint = "https://42fd29e5b225.ngrok-free.app/graphql"
    result = fetch_call_data_transcribe(endpoint)
    print(json.dumps(result, indent=2))
    
