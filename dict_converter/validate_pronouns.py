# validate_pronouns.py

# Canonical pronoun profiles for validation
PRONOUN_PROFILES = {
    # ---------------- SPANISH ----------------
    "es_pres_ind": [
        "yo",
        "tú",
        "él", "ella", "usted",
        "nosotros", "nosotras",
        "vosotros", "vosotras",
        "ellos", "ellas", "ustedes"
    ],
    "es_preterite": [
        "yo",
        "tú",
        "él", "ella", "usted",
        "nosotros", "nosotras",
        "vosotros", "vosotras",
        "ellos", "ellas", "ustedes"
    ],

    # ---------------- FRENCH ----------------
    "fr_pres_ind": [
        "je",
        "tu",
        "il", "elle", "on",
        "nous",
        "vous",
        "ils", "elles"
    ]

    # English is omitted intentionally (pronoun check not enforced)
}
