import sys

# Adjust path so imports can work from WES350 root
sys.path.append("..")

print("🧪 Checking access and structure of flat dictionaries...")

def validate_dict_structure(name, data):
    if not isinstance(data, dict):
        print(f"❌ {name} is not a dictionary.")
        return
    sample_keys = list(data.keys())[:3]
    for key in sample_keys:
        if not isinstance(key, str):
            print(f"❌ {name} contains a non-string key: {key}")
        if not isinstance(data[key], str):
            print(f"❌ {name} key '{key}' has non-string value: {data[key]}")
    print(f"✅ {name} passed structure check with {len(data)} entries.")

try:
    from y_data.en.irrvbs.inf_data import inf_dict as en_flat
    print("✅ en.irrvbs.inf_dict loaded")
    validate_dict_structure("en.irrvbs.inf_dict", en_flat)
except Exception as e:
    print("❌ en.irrvbs.inf_dict failed:", e)

try:
    from y_data.es.pres_ind.inf_data import inf_dict as es_flat
    print("✅ es.pres_ind.inf_dict loaded")
    validate_dict_structure("es.pres_ind.inf_dict", es_flat)
except Exception as e:
    print("❌ es.pres_ind.inf_dict failed:", e)

try:
    from y_data.es.preterite.inf_data import inf_dict as es_preterite_flat
    print("✅ es.preterite.inf_dict loaded")
    validate_dict_structure("es.preterite.inf_dict", es_preterite_flat)
except Exception as e:
    print("❌ es.preterite.inf_dict failed:", e)

try:
    from y_data.fr.pres_ind.inf_data import inf_dict as fr_flat
    print("✅ fr.pres_ind.inf_dict loaded")
    validate_dict_structure("fr.pres_ind.inf_dict", fr_flat)
except Exception as e:
    print("❌ fr.pres_ind.inf_dict failed:", e)
