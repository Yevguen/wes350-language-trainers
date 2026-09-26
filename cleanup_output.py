import os

output_dir = "dict_converter/output"

# Delete all .py and .json files inside output
for filename in os.listdir(output_dir):
    if filename.endswith(".py") or filename.endswith(".json"):
        file_path = os.path.join(output_dir, filename)
        os.remove(file_path)
        print(f"🗑️ Deleted: {file_path}")

print("✅ All converted dictionary files removed.")
