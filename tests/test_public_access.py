import ast
import asyncio
import inspect
from pathlib import Path
from types import SimpleNamespace
from typing import List
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from nicegui import Client, core, ui


def load_functions(filename, names, **globals_):
    """Execute actual functions and language-data imports, without app startup."""
    path = Path(__file__).resolve().parents[1] / filename
    module = ast.parse(path.read_text(encoding="utf-8"))
    nodes = []
    for node in module.body:
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("y_data."):
            nodes.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if names is None or node.name in names:
                node.decorator_list = []
                nodes.append(node)
    namespace = {"ui": ui, **globals_}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace, module


@pytest.fixture
def client():
    instance = Client(ui.page("/__public_access_test__"), request=None)
    try:
        yield instance
    finally:
        instance.delete()


def click(client, text):
    button = next(
        element for element in client.elements.values()
        if isinstance(element, ui.button) and text in element.text
    )
    listener = next(
        listener for listener in button._event_listeners.values()
        if listener.type == "click"
    )
    button._handle_event({"listener_id": listener.id, "args": []})


@pytest.mark.parametrize(
    ("filename", "handler_name", "start", "submit", "reset"),
    [
        ("en200_irrvbs.py", "en_irrvbs_page", "Start Quiz", "Submit Answers", "Reset"),
        ("es350_presind.py", "es_presind_page", "Start Quiz", "Submit Answers", "Reset"),
        ("es200_preterite.py", "es_preterite_page", "Start Quiz", "Submit Answers", "Reset"),
        ("fr200_presind.py", "fr_presind_page", "Démarrer", "Soumettre", "Réinitialiser"),
    ],
)
def test_trainers_construct_and_run_without_auth_or_database(
    client, monkeypatch, filename, handler_name, start, submit, reset
):
    namespace, module = load_functions(filename, None)
    imported_modules = {
        node.module.split(".")[0]
        for node in ast.walk(module)
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name.split(".")[0]
        for node in ast.walk(module) if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not imported_modules & {"auth", "db", "access_utils", "fastapi", "sqlalchemy"}
    assert not any(
        isinstance(node, ast.Name) and node.id in {"check_user_access", "user_has_access"}
        for node in ast.walk(module)
    )
    handler = namespace[handler_name]
    assert not inspect.signature(handler).parameters

    async def exercise():
        # Provide NiceGUI's running-loop context for queued JavaScript responses.
        monkeypatch.setattr(core, "loop", asyncio.get_running_loop())
        with client:
            # No user, session, authentication provider, or access helper is supplied.
            await handler()
            labels = [str(e.text) for e in client.elements.values() if isinstance(e, ui.label)]
            assert "Choose a verb:" in labels
            assert not any("No access" in text for text in labels)
            selector = next(e for e in client.elements.values() if isinstance(e, ui.select))
            verb = next(v for v in namespace["inf_dict"] if v in namespace["vb_forms_dict"])
            selector.value = next(option for option in selector.options if option.startswith(f"{verb} – "))
            click(client, start)

            forms = namespace["vb_forms_dict"][verb]
            inputs = [e for e in client.elements.values() if isinstance(e, ui.input)]
            assert len(inputs) == len(forms)
            for field in inputs:
                field.value = "incorrect-answer"
            click(client, submit)
            labels = [str(e.text) for e in client.elements.values() if isinstance(e, ui.label)]
            assert any("Correct:" in text for text in labels)

            for field in inputs:
                field.value = forms[field.label]
            click(client, submit)
            progress = next(e for e in client.elements.values() if isinstance(e, ui.linear_progress))
            assert progress.value == 1
            click(client, reset)
            assert all(field.value == "" for field in inputs)
            assert progress.value == 0

    asyncio.run(exercise())


def test_login_page_constructs_with_callback(client):
    namespace, _ = load_functions("main.py", {"login_page"})

    async def construct():
        with client:
            await namespace["login_page"]()

    asyncio.run(construct())
    fields = [e.label for e in client.elements.values() if isinstance(e, ui.input)]
    assert fields == ["Email", "Password"]
    login = next(e for e in client.elements.values() if isinstance(e, ui.button))
    assert login.text == "Login"
    assert any(listener.type == "click" for listener in login._event_listeners.values())


async def require_authenticated_user():
    raise HTTPException(status_code=401)


def load_admin(current_user_factory=None, **globals_):
    if current_user_factory is None:
        current_user_factory = lambda **_: require_authenticated_user

    namespace, _ = load_functions(
        "admin_page.py", {"admin_page"},
        Depends=Depends,
        fastapi_users=SimpleNamespace(current_user=current_user_factory),
        User=globals_.pop("User", object),
        UUID=UUID, AsyncSession=object, List=List,
        **globals_,
    )
    return namespace["admin_page"]


def test_admin_requires_active_superuser_dependency():
    requested = {}

    def current_user_factory(**kwargs):
        requested.update(kwargs)
        return require_authenticated_user

    handler = load_admin(current_user_factory=current_user_factory)

    assert requested == {
        "active": True,
        "superuser": True,
    }

    dependency = inspect.signature(handler).parameters["current_user"].default
    assert dependency.dependency is require_authenticated_user

    app = FastAPI()
    app.add_api_route("/admin", handler, methods=["GET"])
    with TestClient(app) as http:
        assert http.get("/admin").status_code == 401


def test_admin_rejects_authenticated_non_superuser(client):
    handler = load_admin()

    async def construct():
        with client:
            await handler(SimpleNamespace(is_superuser=False))

    asyncio.run(construct())
    labels = [e.text for e in client.elements.values() if isinstance(e, ui.label)]
    assert "You must be an admin to access this page." in labels
    assert not any(isinstance(e, ui.button) for e in client.elements.values())


def test_admin_user_controls_have_no_trainer_grants(client):
    # Mock only persistence; render the actual admin UI with a representative user.
    user = SimpleNamespace(
        id=uuid4(), email="admin-test@example.com", is_active=True,
        is_verified=True, is_superuser=True,
    )
    result = MagicMock()
    result.scalars.return_value.all.return_value = [user]
    session = SimpleNamespace(execute=AsyncMock(return_value=result))
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=False)
    handler = load_admin(
        User=SimpleNamespace(email="email"), select=MagicMock(),
        async_session_maker=lambda: session_context,
    )

    async def construct():
        with client:
            await handler(user)

    asyncio.run(construct())
    buttons = {e.text for e in client.elements.values() if isinstance(e, ui.button)}
    assert buttons == {"Create", "Toggle active", "Toggle admin", "Delete"}
    assert not any(isinstance(e, ui.select) for e in client.elements.values())
    session.execute.assert_awaited_once()
