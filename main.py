from download_recordings import download_files,extract_s3_urls_with_callid
from graphql_fetch import fetch_call_data_transcribe
from creating_reference_excel import process_s_id
from compare import mongo_insert
import os
from gemini_processing import process_audio_file  # import your existing function



"""data downloaded from graphql endpoint"""
result = fetch_call_data_transcribe("https://42fd29e5b225.ngrok-free.app/graphql")

    
url_pairs = extract_s3_urls_with_callid(result)
download_files(url_pairs=url_pairs, download_dir="downloads")
"""processing each audio file and inserting into mongo the with s_id as filename"""
folder = "downloads"

for filename in os.listdir(folder):
    process_audio_file(os.path.join(folder, filename),s_id=filename.split(".")[0])

"""
    Given an s_id, fetch corresponding MongoDB record,
    match it with GraphQL call data, and export both
    to a structured Excel file.

    Args:
        s_id (str): The unique identifier to process.
    """
import os
folder = "downloads"
for filename in os.listdir(folder):
    lst=[]
    lst.append(filename.split(".")[0])
    for i in lst:
        process_s_id(i)
        mongo_insert(f"combined.xlsx")