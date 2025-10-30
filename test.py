from download_recordings import download_files,extract_s3_urls_with_callid
from graphql_fetch import fetch_call_data_transcribe
result = fetch_call_data_transcribe("https://42fd29e5b225.ngrok-free.app/graphql")

    
url_pairs = extract_s3_urls_with_callid(result)
download_files(url_pairs=url_pairs, download_dir="downloads")
