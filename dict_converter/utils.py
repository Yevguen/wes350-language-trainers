import os
import json


def convert_flat_to_nested(flat_dict):
    """
    Converts a flat dictionary (e.g., key = 'verb_pronoun') into a nested dictionary:
    {
        'verb': {
            'pronoun': 'form'
        }
    }
    """
    nested_dict = {}
    for compound_key, form in flat_dict.items():
        try:
            verb, pronoun = compound_key.split("_", 1)
        except ValueError:
            print(f"⚠️ Skipping malformed key: {compound_key}")
            continue

        nested_dict.setdefault(verb, {})[pronoun] = form
    return nested_dict


def save_as_py(nested_dict, output_dir, filename):
    """
    Saves the nested dictionary as a Python file with the variable name 'nested_dict'.
    """
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{filename}.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated\n")
        f.write(f"nested_dict = {json.dumps(nested_dict, ensure_ascii=False, indent=2)}\n")
    print(f"💾 Saved Python dictionary: {file_path}")


def save_as_json(nested_dict, output_dir, filename):
    """
    Saves the nested dictionary as a JSON file.
    """
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{filename}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(nested_dict, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved JSON dictionary: {file_path}")
