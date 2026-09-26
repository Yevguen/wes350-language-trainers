# access_utils.py
# Robust access checker for trainer plans; works with both AsyncSession and sync Session.

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

# ---- Configuration ---------------------------------------------------------

ACCESS_MARGIN = timedelta(hours=24)  # +24h grace for start/end edges

ALIASES: Dict[str, str] = {
    "es350": "es350",
    "ES350": "es350",
    "es200": "es200",
    "ES200": "es200",
    "fr200": "fr200",
    "FR200": "fr200",
    "eng200": "en200",
    "ENG200": "en200",  # legacy → new
    "en200": "en200",
    "EN200": "en200",
    "all": "all",
    "ALL": "all",
    "all4": "all",
    "all_trainers": "all",
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def canon(code: str) -> str:
    if not code:
        return ""
    return ALIASES.get(code, ALIASES.get(code.lower(), code.lower()))


def _get_access_model():
    # Lazy import to avoid circulars
    from db import Access

    return Access


def _col(model: Any, *names: str):
    for n in names:
        if hasattr(model, n):
            return getattr(model, n)
    return None


# ---- Core sync implementation ---------------------------------------------


def _sync_user_has_access(session: Session, user: Any, plan_code: str) -> bool:
    """
    - Admins bypass (uses is_superuser, but also honors legacy is_admin if present)
    - 'all' wildcard is accepted
    - +24h grace applied to start/end if present
    - If only end is present, treat end=NULL as unlimited (active)
    - If neither start nor end exist, presence of a row is enough
    """
    # Admin bypass
    if getattr(user, "is_superuser", False) or getattr(user, "is_admin", False):
        return True

    Access = _get_access_model()

    user_id_col = _col(Access, "user_id")
    plan_col = _col(Access, "plan", "trainer")
    start_col = _col(Access, "start_at", "starts_at")
    end_col = _col(Access, "end_at", "expires_at")  # your model uses expires_at
    active_col = _col(Access, "active")

    assert (
        user_id_col is not None and plan_col is not None
    ), "Access model must have user_id and plan/trainer columns."

    code = canon(plan_code)
    now = _now_utc()

    q = (
        session.query(Access.id)
        .filter(user_id_col == getattr(user, "id"))
        .filter(or_(plan_col == code, plan_col == "all"))
    )

    if active_col is not None:
        q = q.filter(active_col.is_(True))

    # Time windows with grace; also treat NULL end as unlimited
    if start_col is not None and end_col is not None:
        q = q.filter(
            or_(
                end_col.is_(None),  # unlimited
                (start_col <= now + ACCESS_MARGIN) & (end_col >= now - ACCESS_MARGIN),
            )
        )
    elif end_col is not None:
        q = q.filter(or_(end_col.is_(None), end_col >= now - ACCESS_MARGIN))
    elif start_col is not None:
        q = q.filter(start_col <= now + ACCESS_MARGIN)
    # else: no time cols → presence of row is enough

    return session.query(q.exists()).scalar()


# ---- Public API: works with both AsyncSession and sync Session -------------


def user_has_access(session: Session, user: Any, plan_code: str) -> bool:
    """Sync-friendly API (kept for completeness)."""
    return _sync_user_has_access(session, user, plan_code)


async def check_user_access(
    user: Any, plan_code: str, session: Session | AsyncSession
) -> bool:
    """
    Back-compat async wrapper using the **original** call order you had:
        await check_user_access(current_user, PLAN_ID, session)

    Accepts either AsyncSession or sync Session.
    """
    if isinstance(session, AsyncSession):
        return await session.run_sync(
            lambda s: _sync_user_has_access(s, user, plan_code)
        )
    elif isinstance(session, Session):
        # Callers might still 'await' this; that's fine in Python but unnecessary.
        return _sync_user_has_access(session, user, plan_code)
    else:
        raise TypeError("session must be a SQLAlchemy Session or AsyncSession")


# Optional helpers remain sync; add async wrappers if you need them.
def list_user_accesses(session: Session, user_id: Any) -> List[Dict[str, Any]]:
    Access = _get_access_model()

    user_id_col = _col(Access, "user_id")
    plan_col = _col(Access, "plan", "trainer")
    start_col = _col(Access, "start_at", "starts_at")
    end_col = _col(Access, "end_at", "expires_at")
    active_col = _col(Access, "active")
    created_col = _col(Access, "created_at")
    id_col = _col(Access, "id")

    q = session.query(Access).filter(user_id_col == user_id)
    if created_col is not None:
        q = q.order_by(created_col.desc())
    elif id_col is not None:
        q = q.order_by(id_col.desc())

    out: List[Dict[str, Any]] = []
    for r in q.all():
        out.append(
            {
                "id": getattr(r, getattr(id_col, "key", "id"), None),
                "user_id": getattr(r, getattr(user_id_col, "key", "user_id"), None),
                "plan": canon(getattr(r, getattr(plan_col, "key", "plan"), "")),
                "start_at": (
                    getattr(r, getattr(start_col, "key", "start_at"), None)
                    if start_col is not None
                    else None
                ),
                "end_at": (
                    getattr(r, getattr(end_col, "key", "end_at"), None)
                    if end_col is not None
                    else None
                ),
                "active": (
                    getattr(r, getattr(active_col, "key", "active"), None)
                    if active_col is not None
                    else None
                ),
                "created_at": (
                    getattr(r, getattr(created_col, "key", "created_at"), None)
                    if created_col is not None
                    else None
                ),
            }
        )
    return out


# Legacy name still available
# (Note: this now points to the async-aware wrapper so old code keeps working.)
# Old signature: await check_user_access(current_user, PLAN, session)
# New code may prefer: await check_user_access(user, plan, async_session)
