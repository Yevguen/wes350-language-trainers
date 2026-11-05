import ast
import asyncio
from pathlib import Path

import pytest
from nicegui import Client, ui

from pages import privacy_page

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PAGES = [
    "main.py",
    "en200_irrvbs.py",
    "es350_presind.py",
    "es200_preterite.py",
    "fr200_presind.py",
]


def links_to(path, target):
    module = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    return [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "link"
        and len(node.args) > 1
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == target
    ]


def test_privacy_page_shows_english_and_spanish_notices():
    client = Client(ui.page("/privacy-test"), request=None)

    async def construct():
        with client:
            privacy_page.privacy_page()

    try:
        asyncio.run(construct())
        texts = [e.content for e in client.elements.values() if isinstance(e, ui.markdown)]
        assert any("## Privacy notice" in t for t in texts)
        assert any("## Aviso de privacidad" in t for t in texts)
    finally:
        client.delete()


def test_privacy_notice_has_no_placeholders():
    for text in (privacy_page.PRIVACY_EN, privacy_page.PRIVACY_ES):
        assert "REPLACE-WITH" not in text
    assert "@" in privacy_page.CONTACT_EMAIL


@pytest.mark.parametrize("path", PUBLIC_PAGES)
def test_every_public_page_links_to_the_privacy_notice(path):
    assert links_to(path, "/privacy")


def test_purchase_page_links_to_the_privacy_notice():
    source = (ROOT / "pages" / "purchase_page.py").read_text(encoding="utf-8")
    assert "](/privacy)" in source


def test_render_start_command_keeps_no_access_log():
    # The privacy notice says the site keeps no request logs; Uvicorn's access
    # log would otherwise record each visitor's forwarded IP address.
    render = (ROOT / "render.yaml").read_text(encoding="utf-8")
    start = next(line for line in render.splitlines() if "startCommand:" in line)
    assert "--no-access-log" in start
