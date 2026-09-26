import ast
import asyncio
import json
from pathlib import Path
import re

import pytest
from nicegui import Client, ui


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("learner@example.test", "ordinary-test-password"),
        ("learner'\"@example.test", "both'\"quotes"),
        (r"learner\name@example.test", r"back\slash\\end"),
        ("line\nbreak@example.test", "line\n\r\t\0\u2028\u2029break"),
        ("'); globalThis.injected = true; //", '\"}); globalThis.injected = true; //'),
    ],
    ids=["ordinary", "quotes", "backslashes", "line-and-control-characters", "injection"],
)
def test_login_callback_serializes_form_values_without_changing_script(
    monkeypatch, email, password
):
    path = Path(__file__).resolve().parents[1] / "main.py"
    module = ast.parse(path.read_text(encoding="utf-8"))
    handler = next(
        node for node in module.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "login_page"
    )
    handler.decorator_list = []
    # Load the real serialization import and handler, without application startup.
    imports = [
        node for node in module.body
        if isinstance(node, ast.Import) and any(a.name == "json" for a in node.names)
    ]
    namespace = {"ui": ui}
    exec(compile(ast.Module(body=[*imports, handler], type_ignores=[]), str(path), "exec"), namespace)
    scripts = []
    monkeypatch.setattr(ui, "run_javascript", scripts.append)
    client = Client(ui.page("/__login_serialization_test__"), request=None)

    async def submit_values():
        with client:
            await namespace["login_page"]()
            inputs = [e for e in client.elements.values() if isinstance(e, ui.input)]
            button = next(e for e in client.elements.values() if isinstance(e, ui.button))
            listener = next(v for v in button._event_listeners.values() if v.type == "click")
            for values in [("baseline@example.test", "baseline-test-password"), (email, password)]:
                for field, value in zip(inputs, values):
                    field.value = value
                button._handle_event({"listener_id": listener.id, "args": []})

    try:
        asyncio.run(submit_values())
    finally:
        client.delete()

    assert len(scripts) == 2

    def split_form_data(script):
        start = re.search(r"new\s+URLSearchParams\s*\(\s*", script)
        assert start is not None
        data, length = json.JSONDecoder().raw_decode(script[start.end():])
        end = start.end() + length
        assert script[end:].lstrip().startswith(")")
        return data, (script[:start.end()], script[end:])

    _, baseline_structure = split_form_data(scripts[0])
    data, structure = split_form_data(scripts[1])
    assert data == {"username": email, "password": password}
    # All input stays within one JSON value; executable code outside it is identical.
    assert structure == baseline_structure

