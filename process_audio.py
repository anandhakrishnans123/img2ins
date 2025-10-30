import os

from gemini_processing import process_audio_file  # import your existing function



# --------------------------------------------

import os

folder = "downloads"

for filename in os.listdir(folder):
    process_audio_file(os.path.join(folder, filename),s_id=filename.split(".")[0])