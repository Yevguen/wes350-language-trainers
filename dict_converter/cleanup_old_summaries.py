import os
import glob

# Folder where logs and summaries are stored
TARGET_DIR = "./output"  # Adjust if needed

# File patterns to delete
patterns = [
    "validation_summary_*.csv",
    "validation_summary_*.json",
    "validation_log_*.txt"
]

deleted = 0
for pattern in patterns:
    full_pattern = os.path.join(TARGET_DIR, pattern)
    for file_path in glob.glob(full_pattern):
        try:
            os.remove(file_path)
            print(f"🗑️ Deleted: {file_path}")
            deleted += 1
        except Exception as e:
            print(f"⚠️ Could not delete {file_path}: {e}")

if deleted == 0:
    print("✅ No old validation files found.")
else:
    print(f"✅ Deleted {deleted} file(s).")
