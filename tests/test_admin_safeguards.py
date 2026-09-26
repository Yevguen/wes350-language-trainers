import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4


class ColumnStub:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return ("eq", self.name, other)


class QueryStub:
    def __init__(self, kind):
        self.kind = kind
        self.select_from_args = ()
        self.where_args = ()

    def select_from(self, *args):
        self.select_from_args = args
        return self

    def where(self, *args):
        self.where_args = args
        return self


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class UserStub:
    is_superuser = ColumnStub("is_superuser")
    is_active = ColumnStub("is_active")


class AccessStub:
    user_id = ColumnStub("user_id")


class FakeSession:
    def __init__(self, target_user=None, active_admin_count=1):
        self.get = AsyncMock(return_value=target_user)
        self.commit = AsyncMock()
        self.delete = AsyncMock()
        self.active_admin_count = active_admin_count
        self.executed_queries = []

    async def execute(self, query):
        self.executed_queries.append(query)

        if query.kind == "select":
            return ScalarResult(self.active_admin_count)

        return SimpleNamespace()


class SessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def load_admin_actions(
    *,
    current_user,
    target_user=None,
    active_admin_count=1,
):
    source_path = Path(__file__).resolve().parents[1] / "admin_page.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))

    admin_page = next(
        node
        for node in module.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "admin_page"
    )

    wanted_names = {
        "count_active_admins",
        "delete_user",
        "toggle_active",
        "toggle_admin",
    }

    nodes = [
        node
        for node in admin_page.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name in wanted_names
    ]

    if {node.name for node in nodes} != wanted_names:
        missing = wanted_names - {node.name for node in nodes}
        raise AssertionError(
            f"Expected admin safeguard functions not found: {sorted(missing)}"
        )

    queries = []

    def select_stub(*_args):
        query = QueryStub("select")
        queries.append(query)
        return query

    def delete_stub(_model):
        query = QueryStub("delete")
        queries.append(query)
        return query

    session = FakeSession(
        target_user=target_user,
        active_admin_count=active_admin_count,
    )

    factory_calls = []

    def session_factory():
        factory_calls.append(True)
        return SessionContext(session)

    notifications = []

    ui_stub = SimpleNamespace(
        notify=lambda message, color=None: notifications.append(
            (message, color)
        )
    )

    refresh_lists = AsyncMock()
    render_refresh = MagicMock()
    render_users_table = SimpleNamespace(refresh=render_refresh)

    namespace = {
        "AsyncSession": object,
        "UUID": UUID,
        "User": UserStub,
        "Access": AccessStub,
        "current_user": current_user,
        "async_session_maker": session_factory,
        "select": select_stub,
        "delete": delete_stub,
        "func": SimpleNamespace(count=lambda: object()),
        "ui": ui_stub,
        "refresh_lists": refresh_lists,
        "render_users_table": render_users_table,
    }

    lifted = ast.Module(body=nodes, type_ignores=[])
    ast.fix_missing_locations(lifted)

    exec(
        compile(lifted, str(source_path), "exec"),
        namespace,
    )

    return SimpleNamespace(
        count_active_admins=namespace["count_active_admins"],
        delete_user=namespace["delete_user"],
        toggle_active=namespace["toggle_active"],
        toggle_admin=namespace["toggle_admin"],
        session=session,
        queries=queries,
        factory_calls=factory_calls,
        notifications=notifications,
        refresh_lists=refresh_lists,
        render_refresh=render_refresh,
    )


def test_active_admin_counter_filters_active_superusers():
    current = SimpleNamespace(id=uuid4())
    runtime = load_admin_actions(
        current_user=current,
        active_admin_count=2,
    )

    result = asyncio.run(
        runtime.count_active_admins(runtime.session)
    )

    assert result == 2

    query = runtime.queries[-1]
    assert query.kind == "select"
    assert len(query.where_args) == 2

    compared_columns = {
        expression[1]
        for expression in query.where_args
    }

    assert compared_columns == {
        "is_superuser",
        "is_active",
    }


def test_admin_cannot_deactivate_own_account():
    current = SimpleNamespace(id=uuid4())

    runtime = load_admin_actions(
        current_user=current,
        target_user=current,
    )

    asyncio.run(runtime.toggle_active(current.id))

    assert runtime.factory_calls == []
    assert runtime.notifications == [
        (
            "You cannot deactivate your own account.",
            "negative",
        )
    ]


def test_last_active_admin_cannot_be_deactivated():
    current = SimpleNamespace(id=uuid4())

    target = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        is_superuser=True,
    )

    runtime = load_admin_actions(
        current_user=current,
        target_user=target,
        active_admin_count=1,
    )

    asyncio.run(runtime.toggle_active(target.id))

    assert target.is_active is True
    runtime.session.commit.assert_not_awaited()

    assert runtime.notifications == [
        (
            "Cannot deactivate the last active admin.",
            "negative",
        )
    ]


def test_admin_can_be_deactivated_when_another_active_admin_exists():
    current = SimpleNamespace(id=uuid4())

    target = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        is_superuser=True,
    )

    runtime = load_admin_actions(
        current_user=current,
        target_user=target,
        active_admin_count=2,
    )

    asyncio.run(runtime.toggle_active(target.id))

    assert target.is_active is False
    runtime.session.commit.assert_awaited_once()
    runtime.refresh_lists.assert_awaited_once()
    runtime.render_refresh.assert_called_once()


def test_last_active_admin_cannot_be_deleted():
    current = SimpleNamespace(id=uuid4())

    target = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        is_superuser=True,
    )

    runtime = load_admin_actions(
        current_user=current,
        target_user=target,
        active_admin_count=1,
    )

    asyncio.run(runtime.delete_user(target.id))

    runtime.session.delete.assert_not_awaited()
    runtime.session.commit.assert_not_awaited()

    assert runtime.notifications == [
        (
            "Cannot delete the last active admin.",
            "negative",
        )
    ]


def test_last_active_admin_cannot_be_demoted():
    current = SimpleNamespace(id=uuid4())

    target = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        is_superuser=True,
    )

    runtime = load_admin_actions(
        current_user=current,
        target_user=target,
        active_admin_count=1,
    )

    asyncio.run(runtime.toggle_admin(target.id))

    assert target.is_superuser is True
    runtime.session.commit.assert_not_awaited()

    assert runtime.notifications == [
        (
            "Cannot remove admin: this is the last active admin.",
            "negative",
        )
    ]
