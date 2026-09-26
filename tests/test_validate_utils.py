from dict_converter.validate_utils import validate_nested_verb_dict


def test_valid_english_dictionary():
    data = {
        "go": {
            "Past Indefinite": "went",
            "Past Participle": "gone",
        }
    }

    assert (
        validate_nested_verb_dict(
            data,
            lang_key="en",
            required_tenses={"Past Indefinite", "Past Participle"},
        )
        is True
    )


def test_english_dictionary_detects_missing_tense():
    data = {
        "go": {
            "Past Indefinite": "went",
        }
    }

    assert (
        validate_nested_verb_dict(
            data,
            lang_key="en",
            required_tenses={"Past Indefinite", "Past Participle"},
        )
        is False
    )


def test_valid_spanish_dictionary():
    data = {
        "ser": {
            "yo": "soy",
            "tú": "eres",
        }
    }

    assert (
        validate_nested_verb_dict(
            data,
            lang_key="es",
            required_pronouns={"yo", "tú"},
        )
        is True
    )


def test_spanish_dictionary_detects_unknown_pronoun():
    data = {
        "ser": {
            "invalid-pronoun": "soy",
        }
    }

    assert (
        validate_nested_verb_dict(
            data,
            lang_key="es",
            required_pronouns={"yo", "tú"},
        )
        is False
    )


def test_dictionary_detects_non_string_form():
    data = {
        "go": {
            "Past Indefinite": 123,
            "Past Participle": "gone",
        }
    }

    assert (
        validate_nested_verb_dict(
            data,
            lang_key="en",
            required_tenses={"Past Indefinite", "Past Participle"},
        )
        is False
    )


def test_french_infinitives_match_conjugation_groups():
    from y_data.fr.pres_ind.inf_data import inf_dict
    from y_data.fr.pres_ind.vb_forms_data import vb_forms_dict

    expected_pronouns = {
        "je",
        "tu",
        "il/elle/on",
        "nous",
        "vous",
        "ils/elles",
    }

    assert len(inf_dict) == 200
    assert len(vb_forms_dict) == 200
    assert set(inf_dict) == set(vb_forms_dict)

    for verb, forms in vb_forms_dict.items():
        assert set(forms) == expected_pronouns, verb
