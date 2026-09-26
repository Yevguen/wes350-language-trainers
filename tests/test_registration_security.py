import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi_users import schemas

from password import get_password_hash


def load_custom_register():
    path = Path(__file__).resolve().parents[1] / "auth_custom_register.py"
    module = ast.parse(path.read_text(encoding="utf-8"))

    handler = next(
        node
        for node in module.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "custom_register"
    )
    handler.decorator_list = []

    def stub_get_user_db():
        raise AssertionError("Dependency injection must not run in this isolated test")

    namespace = {
        "schemas": schemas,
        "Depends": Depends,
        "get_user_db": stub_get_user_db,
        "HTTPException": HTTPException,
        "JSONResponse": JSONResponse,
        "status": status,
        "get_password_hash": get_password_hash,
    }

    exec(
        compile(
            ast.Module(body=[handler], type_ignores=[]),
            str(path),
            "exec",
        ),
        namespace,
    )

    return namespace["custom_register"]


class FakeUserDB:
    def __init__(self):
        self.created = None

    async def get_by_email(self, _email):
        return None

    async def create(self, user_dict):
        self.created = dict(user_dict)
        return SimpleNamespace(email=user_dict["email"])


@pytest.mark.parametrize(
    "privileged_input",
    [
        {"is_superuser": True},
        {"is_active": False},
        {"is_verified": False},
    ],
)
def test_public_registration_cannot_control_privileged_flags(privileged_input):
    register = load_custom_register()
    user_db = FakeUserDB()

    user = schemas.BaseUserCreate(
        email="security-test@example.com",
        password="test-password-123",
        **privileged_input,
    )

    asyncio.run(register(user, user_db))

    created = user_db.created
    assert created is not None

    assert created["is_superuser"] is False
    assert created["is_active"] is True
    assert created["is_verified"] is True

    assert "password" not in created
    assert created["hashed_password"] != "test-password-123"
