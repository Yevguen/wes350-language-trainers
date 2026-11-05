import ast
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from nicegui import Client, ui

ROOT = Path(__file__).resolve().parents[1]


def test_register_page_shows_closed_notice_without_form():
    source_path = ROOT / "main.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    handler = next(
        node
        for node in module.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "register_page"
    )

    # Execute the actual handler body without importing main's database/auth setup
    # or registering a global route.
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
        elements = list(client.elements.values())
        assert not any(isinstance(e, (ui.input, ui.button)) for e in elements)
        labels = [e.text for e in elements if isinstance(e, ui.label)]
        assert "Registration is closed." in labels
    finally:
        client.delete()


def test_home_page_has_no_register_link():
    module = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
    register_links = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "link"
        and len(node.args) > 1
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == "/register"
    ]
    assert register_links == []


APP_CHECK = r"""
import asyncio, json
import db
asyncio.run(db.create_all_tables())
import main
from fastapi.testclient import TestClient
from sqlalchemy import func, select

async def count_users():
    async with db.async_session_maker() as session:
        return (await session.execute(select(func.count()).select_from(db.User))).scalar_one()

with TestClient(main.app) as http:
    register = http.post(
        "/auth/register",
        json={"email": "visitor@example.com", "password": "visitor-pass-123"},
    )
    login = http.post(
        "/auth/login",
        data={"username": "admin@example.com", "password": "admin-pass-123"},
    )
print(json.dumps({
    "register": register.status_code,
    "login": login.status_code,
    "users": asyncio.run(count_users()),
}))
"""


def test_app_has_no_registration_endpoint_and_admin_login_works(tmp_path):
    env = {
        **os.environ,
        "SECRET": "test-secret-not-for-production",
        "DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'app.db'}",
        "ADMIN_EMAIL": "admin@example.com",
        "ADMIN_PASSWORD": "admin-pass-123",
    }
    # A separate process keeps main's global NiceGUI and database setup out of
    # the other tests.
    result = subprocess.run(
        [sys.executable, "-c", APP_CHECK],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    outcome = json.loads(result.stdout.strip().splitlines()[-1])
    assert outcome["register"] in (404, 405)
    assert outcome["login"] == 204
    assert outcome["users"] == 1
