import ast
import asyncio
from pathlib import Path

from nicegui import Client, ui


def test_register_page_constructs_with_submit_callback():
    source_path = Path(__file__).resolve().parents[1] / "main.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    handler = next(
        node
        for node in module.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "register_page"
    )

    # Execute the actual handler body without importing main's database/auth setup
    # or registering a global route. UI elements and callback binding are real.
    handler.decorator_list = []
    namespace = {"ui": ui}
    exec(
        compile(ast.Module(body=[handler], type_ignores=[]), str(source_path), "exec"),
        namespace,
    )

    client = Client(ui.page("/register"), request=None)

    async def construct_page():
        with client:
            await namespace["register_page"]()

    try:
        asyncio.run(construct_page())
        buttons = [
            element
            for element in client.elements.values()
            if isinstance(element, ui.button)
        ]
        assert len(buttons) == 1
        assert buttons[0].text == "Register"
        assert any(
            listener.type == "click"
            for listener in buttons[0]._event_listeners.values()
        )
    finally:
        client.delete()
