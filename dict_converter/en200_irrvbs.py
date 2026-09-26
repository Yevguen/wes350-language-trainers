from nicegui import ui
from y_data.en.irrvbs.inf_data import inf_dict 
from y_data.en.irrvbs.vb_forms_data import vb_forms_dict

# Helper functions (can remain at module level if they don't depend on page-specific UI state)
def get_conjugation_keys(verb: str, current_vb_forms_dict: dict) -> list[str]:
    keys = [key for key in current_vb_forms_dict if key.startswith(f"{verb}_")]
    return sorted(keys, key=lambda k: ("Participle" in k, k))

def score_conjugation(user_inputs: dict[str, str], correct_forms: dict[str, str]) -> tuple[int, list[tuple[str,str,str,bool]]]:
    results = []
    score = 0
    for tense, correct in correct_forms.items():
        answer = user_inputs.get(tense, "").strip().lower()
        correct_str = correct.strip().lower()
        options = [opt.strip().lower() for opt in correct_str.split("/")] # Handle multiple correct answers
        is_correct = (answer == correct_str) or (answer in options)
        results.append((tense, answer, correct, is_correct))
        if is_correct:
            score += 1
    return score, results

@ui.page('/en/irregular')
def en_irregular_page():
    # Page-specific state
    quiz_form_inputs: dict[str, ui.input] = {}
    
    # Main UI container for this page
    with ui.column().classes("items-center p-4 md:p-8 max-w-2xl mx-auto"): # Responsive padding and max-width
        ui.button('⬅️ Back to Menu', on_click=lambda: ui.navigate.to('/')).classes('absolute top-4 left-4')
        ui.icon('translate', size='4rem').classes('text-blue-500 m-4')
        ui.label("🇬🇧 English Irregular Verbs Trainer").classes("text-3xl font-bold mb-6 text-center")

        # Area for quiz setup (verb selection)
        quiz_setup_area = ui.column().classes('w-full items-center')
        # Area for the active quiz (inputs)
        active_quiz_area = ui.column().classes('w-full items-center')
        # Area for displaying results
        result_display_area = ui.column().classes("w-full mt-6")

        def display_results(verb: str, keys: list[str]):
            result_display_area.clear()
            user_inputs_values = {tense: field.value for tense, field in quiz_form_inputs.items()}
            correct_forms = vb_forms_dict[verb]
            
            score, detailed_results = score_conjugation(user_inputs_values, correct_forms)

            with result_display_area:
                ui.notify(f"Final Score for {verb}: {score}/{len(detailed_results)}", color="blue" if score == len(detailed_results) else "orange")
                with ui.card().classes("w-full shadow-lg mt-4 p-4"):
                    ui.label("📝 Quiz Results").classes("text-xl font-semibold mb-3 text-center")
                    for tense, answer, correct_answer, is_ok in detailed_results:
                        color = "green" if is_ok else "red"
                        emoji = "✅" if is_ok else "❌"
                        with ui.row().classes('items-center w-full'):
                            ui.label(f"{tense}:").classes('w-1/3 font-medium')
                            ui.label(f"{answer or '—'} {emoji}").style(f"color: {color}").classes('w-1/3')
                            if not is_ok:
                                ui.label(f"(Correct: {correct_answer})").classes('w-1/3 text-xs text-gray-600')
                            else:
                                ui.label().classes('w-1/3') # Placeholder for alignment

        def build_quiz_inputs(verb: str):
            active_quiz_area.clear()
            result_display_area.clear()
            quiz_form_inputs.clear()

            if not verb:
                ui.notify("Please select a verb!", color="negative")
                return

            if verb not in vb_forms_dict:
                ui.notify(f"No conjugation data found for {verb}!", color="negative")
                return
            keys = list(vb_forms_dict[verb].keys())
            
            with active_quiz_area:
                with ui.card().classes("w-full shadow-md p-6 bg-gray-50"):
                    ui.label(f"Conjugate the verb: {verb.upper()}").classes("text-2xl font-semibold mb-4 text-center text-blue-600")
                    for key in keys:
                        tense = key.split("_", 1)[1].replace("_", " ").title() # Make tense more readable
                        quiz_form_inputs[tense] = ui.input(label=tense).classes("w-full mb-2")
                    
                    ui.button(
                        "✅ Submit Answers",
                        on_click=lambda: display_results(verb, keys),
                        color='positive'
                    ).classes("mt-4 w-full p-3 text-lg")

        with quiz_setup_area:
            with ui.card().classes("w-full md:w-96 shadow-xl p-6"): # Responsive width for card
                ui.label("Choose a verb:").classes("text-xl mb-3 font-semibold")
                
                # Prepare options for the select dropdown
                verb_options_map = {
                    f"{v_key} – {', '.join(v_defs[:2])}": v_key # Show first two definitions
                    for v_key, v_defs in inf_dict.items()
                    if isinstance(v_defs, list) and len(v_defs) >= 1
                }
                
                if not verb_options_map:
                    ui.label("No verbs loaded. Check y_data/en/irrvbs/inf_dict.py").classes("text-red-500")
                    return # Stop if no verbs

                selected_verb_display = ui.select(
                    options=list(verb_options_map.keys()), 
                    label="Infinitive",
                    with_input=True # Allows typing to filter
                ).classes("w-full mb-4")
                
                ui.button(
                    "🚀 Start Quiz",
                    on_click=lambda: build_quiz_inputs(verb_options_map.get(selected_verb_display.value, "")),
                    color='primary'
                ).classes("w-full p-3 text-lg")

