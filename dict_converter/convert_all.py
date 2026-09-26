import sys
import os
import argparse
import csv
import json
import yaml  # Requires PyYAML
from utils import convert_flat_to_nested

# Ensure the parent directory is on sys.path for imports
sys.path.insert(0, os.path.abspath("."))

# Imports from updated data files
from y_data.en.irrvbs.vb_forms_data import vb_forms_dict as en_forms
from y_data.es.pres_ind.vb_forms_data import vb_forms_dict as es_pres_forms
from y_data.es.preterite.vb_forms_data import vb_forms_dict as es_pret_forms
from y_data.fr.pres_ind.vb_forms_data import vb_forms_dict as fr_forms

AVAILABLE_DICTIONARIES = {
    "en": en_forms,
    "es_pres": es_pres_forms,
    "es_pret": es_pret_forms,
    "fr": fr_forms,
}

def save_as_py(nested_dict, output_dir, filename):
    path = os.path.join(output_dir, f"{filename}.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated\n")
        f.write(f"nested_dict = {json.dumps(nested_dict, ensure_ascii=False, indent=2)}\n")
    print(f"💾 Saved: {path}")

def save_as_json(nested_dict, output_dir, filename):
    path = os.path.join(output_dir, f"{filename}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nested_dict, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved: {path}")

def save_as_yaml(nested_dict, output_dir, filename):
    path = os.path.join(output_dir, f"{filename}.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(nested_dict, f, allow_unicode=True, sort_keys=False)
    print(f"💾 Saved: {path}")

def save_as_csv(nested_dict, output_dir, filename):
    path = os.path.join(output_dir, f"{filename}.csv")
    with open(path, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["verb", "tense", "form"])
        for verb, forms in nested_dict.items():
            for tense, form in forms.items():
                writer.writerow([verb, tense, form])
    print(f"💾 Saved: {path}")

def convert_and_save(lang_key, flat_dict, output_dir, formats):
    print(f"\n🔍 Converting: {lang_key}")
    nested = convert_flat_to_nested(flat_dict)
    print(f"✅ Nested structure with {len(nested)} verbs")

    filename = f"{lang_key}_data"

    if "py" in formats:
        save_as_py(nested, output_dir, filename)
    if "json" in formats:
        save_as_json(nested, output_dir, filename)
    if "yaml" in formats:
        save_as_yaml(nested, output_dir, filename)
    if "csv" in formats:
        save_as_csv(nested, output_dir, filename)

def main():
    parser = argparse.ArgumentParser(description="Convert verb dictionaries into various formats.")
    parser.add_argument("--lang", choices=AVAILABLE_DICTIONARIES.keys(), help="Convert a specific language only")
    parser.add_argument("--output", default="dict_converter/output", help="Output directory")
    parser.add_argument("--formats", nargs="+", default=["py", "json"], help="Output formats: py json yaml csv")

    args = parser.parse_args()
    os.makedirs(args.output, exist_ok=True)

    if args.lang:
        convert_and_save(args.lang, AVAILABLE_DICTIONARIES[args.lang], args.output, args.formats)
    else:
        for lang_key, flat_dict in AVAILABLE_DICTIONARIES.items():
            convert_and_save(lang_key, flat_dict, args.output, args.formats)

    print(f"\n✅ All requested conversions saved to: {os.path.abspath(args.output)}")

if __name__ == "__main__":
    main()
