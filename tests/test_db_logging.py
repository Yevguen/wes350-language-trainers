import ast
import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine


def test_database_engine_disables_sql_echo():
    path = Path(__file__).resolve().parents[1] / "db.py"
    module = ast.parse(path.read_text(encoding="utf-8"))
    engine_setup = next(
        node for node in module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "engine" for target in node.targets)
    )
    # Execute the actual engine configuration with a local URL, without .env,
    # model imports, application startup, or a database connection.
    namespace = {
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "create_async_engine": create_async_engine,
    }
    exec(compile(ast.Module(body=[engine_setup], type_ignores=[]), str(path), "exec"), namespace)
    engine = namespace["engine"]
    try:
        assert engine.echo is False
        assert engine.sync_engine.echo is False
    finally:
        asyncio.run(engine.dispose())
