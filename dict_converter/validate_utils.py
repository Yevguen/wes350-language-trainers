import json

def validate_nested_verb_dict(
    nested_dict,
    lang_key=None,
    required_tenses=None,
    required_pronouns=None,
    preview_limit=5,
    log_stream=None,
    log_errors_only=False,
    return_summary=False
):
    success = True
    issues = []

    def log(msg):
        if log_stream:
            log_stream.write(msg + '\n')
        else:
            print(msg)

    # Validate top-level structure
    if not isinstance(nested_dict, dict):
        log("❌ Top-level structure must be a dictionary.")
        return False

    # Preview entries
    sample_keys = list(nested_dict.keys())[:preview_limit]
    log(f"🔍 Previewing {lang_key.upper() if lang_key else ''} sample keys and values:")
    for i, key in enumerate(sample_keys, 1):
        log(f"{i}. {key}: {nested_dict[key]}")

    for verb, forms in nested_dict.items():
        if not isinstance(verb, str) or not isinstance(forms, dict):
            issues.append((verb, "Invalid type"))
            if not log_errors_only:
                log(f"❌ {verb} ➜ invalid structure (expected nested dict)")
            success = False
            continue

        # Check tenses or pronouns
        form_keys = set(forms.keys())

        # English tense validation
        if required_tenses and lang_key == "en":
            missing_tenses = required_tenses - form_keys
            if missing_tenses:
                issues.append((verb, f"Missing tenses: {sorted(missing_tenses)}"))
                if not log_errors_only:
                    log(f"❌ {verb} ➜ missing tenses: {sorted(missing_tenses)}")
                success = False

        for subkey, form in forms.items():
            # Validate form type
            if not isinstance(form, str):
                issues.append((f"{verb}_{subkey}", "Invalid form type"))
                if not log_errors_only:
                    log(f"❌ {verb}_{subkey} ➜ form is not a string")
                success = False

            # Non-English pronoun check
            if required_pronouns and lang_key != "en":
                pronoun = subkey.strip().lower()
                if pronoun not in required_pronouns:
                    issues.append((f"{verb}_{subkey}", "Unknown pronoun"))
                    if not log_errors_only:
                        log(f"❌ {verb}_{subkey} ➜ unknown pronoun '{pronoun}'")
                    success = False

    if success:
        log(f"✅ {lang_key.upper()} dictionary is valid.")
    else:
        log(f"❌ {lang_key.upper()} dictionary has structural issues.")

    return {"success": success, "issues": issues} if return_summary else success
