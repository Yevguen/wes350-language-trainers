import os
import sys
import datetime
import csv
from validate_utils import validate_nested_verb_dict

# Updated imports to match renamed files and variables
from output.en_data import nested_dict as en_dict
from output.es_pres_data import nested_dict as es_pres_dict
from output.es_pret_data import nested_dict as es_pret_dict
from output.fr_data import nested_dict as fr_dict

# Ensure output path is valid
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_dir = "output"
os.makedirs(log_dir, exist_ok=True)
log_filename = os.path.join(log_dir, f"validation_summary_{timestamp}.csv")

# Required structures per language/tense
PRONOUN_PROFILES = {
    "es": [
        "yo", "tú", "él/ella/usted", "nosotros/nosotras",
        "vosotros/vosotras", "ellos/ellas/ustedes"
    ],
    "fr": ["je", "tu", "il/elle/on", "nous", "vous", "ils/elles"]
}
TENSES = {"Past Indefinite", "Past Participle"}

def validate_file(lang_key, file_stub, nested_dict):
    print(f"\n🔍 Validating {lang_key.upper()} dictionary...")

    required_pronouns = PRONOUN_PROFILES.get(lang_key) if lang_key != "en" else None

    with open(log_filename, mode="a", newline='', encoding="utf-8") as log_file:
        writer = csv.writer(log_file)
        writer.writerow(["Language", "Verb", "Issue"])

        result = validate_nested_verb_dict(
            nested_dict,
            lang_key=lang_key,
            required_tenses=TENSES if lang_key == "en" else None,
            required_pronouns=required_pronouns,
            log_stream=log_file,
            preview_limit=3,
            log_errors_only=True,
            return_summary=True
        )

        if result and result["issues"]:
            print(f"❌ {file_stub} has issues.")
            for verb, issue in result["issues"]:
                writer.writerow([lang_key, verb, issue])
        else:
            print(f"✅ {file_stub} is valid.\n")

# Run validations
validate_file("en", "en_data", en_dict)
validate_file("es", "es_pres_data", es_pres_dict)
validate_file("es", "es_pret_data", es_pret_dict)
validate_file("fr", "fr_data", fr_dict)

print(f"\n📄 Validation summary saved to: {log_filename}")
