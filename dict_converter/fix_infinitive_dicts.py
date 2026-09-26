import sys
from collections import defaultdict
import pprint
import json

# Enable access to WES350 project
sys.path.append("..")

print("🔧 Fixing malformed infinitive dictionaries...")

def fix_flat_dict(flat_dict):
    fixed = defaultdict(list)
    for key, value in flat_dict.items():
        base = key.split("_")[0]
        fixed[base].append(value)
    return dict(fixed)

def save_fixed_versions(lang, fixed_dict):
    py_file = f"{lang}_fixed_inf_dict.py"
    json_file = f"{lang}_fixed_inf_dict.json"

    with open(py_file, "w", encoding="utf-8") as f_py:
        f_py.write("# Auto-fixed malformed flat infinitive dictionary\n")
        f_py.write(f"inf_dict = ")
        f_py.write(pprint.pformat(fixed_dict, indent=2))

    with open(json_file, "w", encoding="utf-8") as f_json:
        json.dump(fixed_dict, f_json, ensure_ascii=False, indent=2)

# Attempt fixes
try:
    from y_data.en.irrvbs.inf_data import inf_dict as en_inf
    en_fixed = fix_flat_dict(en_inf)
    save_fixed_versions("en", en_fixed)
    print("✅ en.irrvbs.inf_dict fixed and saved.")
except Exception as e:
    print("❌ en.irrvbs.inf_dict error:", e)

try:
    from y_data.es.pres_ind.inf_data import inf_dict as es_inf
    es_fixed = fix_flat_dict(es_inf)
    save_fixed_versions("es_pres_ind", es_fixed)
    print("✅ es.pres_ind.inf_dict fixed and saved.")
except Exception as e:
    print("❌ es.pres_ind.inf_dict error:", e)

try:
    from y_data.es.preterite.inf_data import inf_dict as es_pret_inf
    es_pret_fixed = fix_flat_dict(es_pret_inf)
    save_fixed_versions("es_preterite", es_pret_fixed)
    print("✅ es.preterite.inf_dict fixed and saved.")
except Exception as e:
    print("❌ es.preterite.inf_dict error:", e)

try:
    from y_data.fr.pres_ind.inf_data import inf_dict as fr_inf
    fr_fixed = fix_flat_dict(fr_inf)
    save_fixed_versions("fr", fr_fixed)
    print("✅ fr.pres_ind.inf_dict fixed and saved.")
except Exception as e:
    print("❌ fr.pres_ind.inf_dict error:", e)
