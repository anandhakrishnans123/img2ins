import requests
import json
import os
from datetime import datetime, timezone

def fetch_and_download_by_date_created(
    url: str = "https://42fd29e5b225.ngrok-free.app/graphql",
    from_date: str = None,
    to_date: str = None,
    download_dir: str = "downloads"
):
    """
    Fetch call transcription data from GraphQL, filter by dateCreatedInUpdates, 
    and download matching files.

    Args:
        url (str): GraphQL endpoint.
        from_date (str): Start date in YYYY-MM-DD or full ISO format.
        to_date (str): End date in YYYY-MM-DD or full ISO format.
        download_dir (str): Directory to save downloads.

    Returns:
        list: List of downloaded file paths.
    """

    # --- Convert string date to UTC datetime ---
    def _to_datetime(date_str):
        if not date_str:
            return None
        try:
            if "T" in date_str:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(timezone.utc)
            else:
                return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception as e:
            raise ValueError(f"Invalid date format for '{date_str}': {e}")

    from_dt = _to_datetime(from_date)
    to_dt = _to_datetime(to_date)

    # --- Fetch all call data ---
    query = """
    query {
        getCallDataTranscribe {
            entityName
            callId
            Recordings {
                s3Url
                dateCreatedInUpdates
            }
        }
    }
    """

    headers = {"Content-Type": "application/json"}

    print("📡 Fetching data from GraphQL...")
    try:
        response = requests.post(url, json={"query": query}, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return []

    all_records = data.get("data", {}).get("getCallDataTranscribe", [])
    if not all_records:
        print("⚠️ No records returned from API.")
        return []

    print(f"✅ Total records fetched: {len(all_records)}")

    # --- Prepare download directory ---
    os.makedirs(download_dir, exist_ok=True)
    downloaded_files = []

    # --- Filter and download ---
    for record in all_records:
        entity = record.get("entityName", "unknown_entity").replace(" ", "_")
        call_id = record.get("callId", "unknown_call")

        for rec in record.get("Recordings", []):
            s3_url = rec.get("s3Url")
            date_str = rec.get("dateCreatedInUpdates")

            if not s3_url or not date_str:
                continue

            try:
                rec_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(timezone.utc)
            except Exception:
                continue

            if from_dt and rec_dt < from_dt:
                continue
            if to_dt and rec_dt > to_dt:
                continue

            # --- Download the file ---
            file_ext = os.path.splitext(s3_url.split("?")[0])[1] or ".mp3"
            # Use s_id (call_id) as the main part of the filename
            filename = f"{call_id}{file_ext}"
            filepath = os.path.join(download_dir, filename)

            try:
                res = requests.get(s3_url, stream=True)
                res.raise_for_status()
                with open(filepath, "wb") as f:
                    for chunk in res.iter_content(8192):
                        f.write(chunk)
                downloaded_files.append(filepath)
                print(f"🎧 Downloaded: {filename}")
            except Exception as e:
                print(f"⚠️ Failed to download {s3_url}: {e}")

    print(f"\n🎉 Total files downloaded: {len(downloaded_files)}")
    return downloaded_files


# --- Example Usage ---
if __name__ == "__main__":
    downloaded = fetch_and_download_by_date_created(
        from_date="2025-10-01",
        to_date="2025-10-29"
    )
    print(json.dumps(downloaded, indent=2))
