import json
import os

# Configurable
REQUIRED_KEYS = {"Past Indefinite", "Past Participle"}
PLACEHOLDER = "__MISSING__"

def patch_verb_dict(input_dict: dict, required_keys=REQUIRED_KEYS, placeholder=PLACEHOLDER):
    patched = {}
    for verb, forms in input_dict.items():
        if not isinstance(forms, dict):
            continue
        patched[verb] = forms.copy()
        missing = required_keys - forms.keys()
        for key in missing:
            patched[verb][key] = placeholder
    return patched

def patch_and_save(input_dict, output_path, var_name="nested_pres_ind_dict"):
    patched = patch_verb_dict(input_dict)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Auto-patched dictionary with missing keys filled\n{var_name} = ")
        json.dump(patched, f, ensure_ascii=False, indent=2)
    print(f"✅ Patched dictionary saved to {output_path}")
