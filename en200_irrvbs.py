from nicegui import ui
from y_data.en.irrvbs.inf_data import inf_dict
from y_data.en.irrvbs.vb_forms_data import vb_forms_dict


# --- helpers (module scope) ---
def score_conjugation(
    user_inputs: dict[str, str], correct_forms: dict[str, str]
) -> tuple[int, list[tuple[str, str, str, bool]]]:
    results = []
    score = 0
    for tense, correct in correct_forms.items():
        answer = user_inputs.get(tense, "").strip().lower()
        correct_str = correct.strip().lower()
        options = [opt.strip().lower() for opt in correct_str.split("/")]
        is_correct = (answer == correct_str) or (answer in options)
        results.append((tense, answer, correct, is_correct))
        if is_correct:
            score += 1
    return score, results


ui.add_head_html(
    """
<style>
@keyframes flash-green {
    0% { background-color: #d4edda; }
    100% { background-color: transparent; }
}
@keyframes shake {
    0% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    50% { transform: translateX(5px); }
    75% { transform: translateX(-5px); }
    100% { transform: translateX(0); }
}
.flash-green { animation: flash-green 0.5s ease; }
.shake { animation: shake 0.5s; }
</style>
"""
)

ui.add_head_html(
    """
<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
"""
)


@ui.page("/en/irrvbs")
async def en_irrvbs_page():
    quiz_form_inputs = {}
    result_display_area = ui.column().classes("w-full mt-6")
    live_score_label = ui.label().classes(
        "text-lg font-medium text-center text-blue-700 mb-2"
    )
    result_label = ui.label().classes("text-xl text-center font-semibold mt-2")
    summary_bar = ui.linear_progress().classes("w-full h-4 mb-2")

    with ui.column().classes("items-center p-4 md:p-8 max-w-2xl mx-auto"):
        ui.button("⬅️ Back to Menu", on_click=lambda: ui.navigate.to("/")).classes(
            "absolute top-4 left-4"
        )
        ui.link("Privacy", "/privacy").classes("absolute top-4 right-4 text-sm")
        ui.icon("translate", size="4rem").classes("text-blue-500 m-4")
        ui.label("🇬🇧 English Irregular Verbs Conjugation Trainer").classes(
            "text-3xl font-bold mb-6 text-center"
        )

        quiz_setup_area = ui.column().classes("w-full items-center")
        active_quiz_area = ui.column().classes("w-full items-center")

        with quiz_setup_area:
            with ui.card().classes("w-full md:w-96 shadow-xl p-6"):
                ui.label("Choose a verb:").classes("text-xl mb-3 font-semibold")

                verb_options_map = {
                    f"{v_key} – {', '.join(v_defs[:2])}": v_key
                    for v_key, v_defs in inf_dict.items()
                    if isinstance(v_defs, list) and len(v_defs) >= 1
                }

                if not verb_options_map:
                    ui.label(
                        "No verbs loaded. Check y_data/en/irrvbs/inf_data.py"
                    ).classes("text-red-500")
                    return

                selected_verb_display = ui.select(
                    options=list(verb_options_map.keys()),
                    label="Infinitive",
                    with_input=True,
                ).classes("w-full mb-4")

                def build_quiz_inputs():
                    active_quiz_area.clear()
                    result_display_area.clear()
                    quiz_form_inputs.clear()
                    result_label.set_text("")
                    summary_bar.value = 0

                    chosen_label = selected_verb_display.value
                    verb = verb_options_map.get(chosen_label, "")
                    if not verb or verb not in vb_forms_dict:
                        ui.notify(
                            f"No conjugation data found for {verb}!", color="negative"
                        )
                        return

                    correct_forms = vb_forms_dict[verb]
                    keys = list(correct_forms.keys())

                    with active_quiz_area:
                        with ui.card().classes("w-full shadow-md p-6 bg-gray-50"):
                            ui.label(f"Conjugate: {verb.upper()}").classes(
                                "text-2xl font-semibold mb-4 text-center text-blue-600"
                            )
                            for tense in keys:
                                input_field = ui.input(label=tense).classes(
                                    "w-full mb-2"
                                )
                                quiz_form_inputs[tense] = input_field

                    def reset_quiz():
                        for field in quiz_form_inputs.values():
                            field.value = ""
                            field.classes(remove="flash-green")
                            field.classes(remove="shake")
                        live_score_label.set_text(f"✅ 0 of {len(keys)} correct")
                        result_label.set_text("")
                        summary_bar.value = 0
                        result_display_area.clear()

                    def display_results():
                        result_display_area.clear()
                        user_inputs_values = {
                            tense: field.value
                            for tense, field in quiz_form_inputs.items()
                        }
                        score, detailed_results = score_conjugation(
                            user_inputs_values, correct_forms
                        )
                        progress = (
                            score / len(detailed_results)
                            if len(detailed_results)
                            else 0
                        )
                        ui.run_javascript(
                            f"""
try {{
    if ({score} === {len(detailed_results)}) {{
        confetti({{
            particleCount: 150,
            spread: 70,
            origin: {{ y: 0.6 }}
        }});
    
"""
                        )
                        summary_bar.value = progress
                        summary_bar.color = (
                            "green" if score == len(detailed_results) else "orange"
                        )
                        result_label.set_text(
                            f"{'🎉 Perfect!' if score == len(detailed_results) else '🔁 Try again!'} You scored {score}/{len(detailed_results)}."
                        )
                        with result_display_area:
                            ui.notify(
                                f"Final Score for {verb}: {score}/{len(detailed_results)}",
                                color=(
                                    "blue"
                                    if score == len(detailed_results)
                                    else "orange"
                                ),
                            )
                            with ui.card().classes("w-full shadow-lg mt-4 p-4"):
                                ui.label("📝 Quiz Results").classes(
                                    "text-xl font-semibold mb-3 text-center"
                                )
                                for (
                                    tense,
                                    answer,
                                    correct_answer,
                                    is_ok,
                                ) in detailed_results:
                                    color = "green" if is_ok else "red"
                                    emoji = "✅" if is_ok else "❌"
                                    with ui.row().classes("items-center w-full"):
                                        ui.label(f"{tense}:").classes(
                                            "w-1/3 font-medium"
                                        )
                                        ui.label(f"{answer or '—'} {emoji}").style(
                                            f"color: {color}"
                                        ).classes("w-1/3")
                                        if not is_ok:
                                            ui.label(
                                                f"(Correct: {correct_answer})"
                                            ).classes("w-1/3 text-xs text-gray-600")
                                        else:
                                            ui.label().classes("w-1/3")

                    ui.button(
                        "🔄 Reset", on_click=reset_quiz, color="secondary"
                    ).classes("mt-2 w-full p-3 text-md")

                    ui.button(
                        "✅ Submit Answers", on_click=display_results, color="positive"
                    ).classes("mt-4 w-full p-3 text-lg")

                ui.button(
                    "🚀 Start Quiz", on_click=build_quiz_inputs, color="primary"
                ).classes("w-full p-3 text-lg")
