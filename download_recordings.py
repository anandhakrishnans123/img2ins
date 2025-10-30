import os
import json
import requests
import shutil
from graphql_fetch import fetch_call_data_transcribe


def extract_s3_urls_with_callid(data, current_call_id=None):
    """
    Recursively extract tuples of (callId, s3Url) from nested JSON data.
    """
    results = []
    if isinstance(data, dict):
        call_id = data.get("callId", current_call_id)
        for key, value in data.items():
            if key == "s3Url" and isinstance(value, str):
                results.append((call_id, value))
            else:
                results.extend(extract_s3_urls_with_callid(value, call_id))
    elif isinstance(data, list):
        for item in data:
            results.extend(extract_s3_urls_with_callid(item, current_call_id))
    return results


def clear_directory(path):
    """
    Deletes all contents of a directory without deleting the folder itself.
    """
    if os.path.exists(path):
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"⚠️ Failed to delete {file_path}: {e}")
    else:
        os.makedirs(path)


def download_files(url_pairs, download_dir="downloads"):
    """
    Downloads all files from the given (callId, s3Url) pairs into the specified folder.
    """
    # 1️⃣ Empty the directory first
    clear_directory(download_dir)

    # 2️⃣ Proceed with download
    os.makedirs(download_dir, exist_ok=True)
    downloaded_files = []

    for i, (call_id, url) in enumerate(url_pairs, start=1):
        try:
            if not call_id:
                call_id = f"unknown_{i}"
            # Use s_id as filename if available, fallback to callId
            filename = f"{call_id}.mp3"  # Default extension, using callId (which is s_id)
            file_path = os.path.join(download_dir, filename)

            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✅ Downloaded: {file_path}")
                downloaded_files.append(file_path)
            else:
                print(f"⚠️ Failed to download ({response.status_code}): {url}")

        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")

    print(f"\n🎉 Total files downloaded: {len(downloaded_files)}")
    return downloaded_files


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # 1. Fetch JSON from GraphQL
    result = fetch_call_data_transcribe("https://42fd29e5b225.ngrok-free.app/graphql")

    # 2. Extract (callId, s3Url) pairs
    url_pairs = extract_s3_urls_with_callid(result)
    print(f"\n🔗 Found {len(url_pairs)} files to download")

    # 3. Download all files
    downloaded_files = download_files(url_pairs)

    # 4. Optional: Output summary as JSON
    print(json.dumps(downloaded_files, indent=2))
