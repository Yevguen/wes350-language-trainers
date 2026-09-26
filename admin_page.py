# admin_page.py
from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import Depends
from nicegui import ui
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth import fastapi_users
from db import Access, User, async_session_maker
from password import get_password_hash


@ui.page("/admin")
async def admin_page(
    current_user: User = Depends(
        fastapi_users.current_user(active=True, superuser=True)
    ),
) -> None:
    """Admin dashboard for managing users."""
    if not current_user.is_superuser:
        with ui.card().classes("m-6 p-6"):
            ui.label("You must be an admin to access this page.")
        return

    # -------------------- state --------------------
    users: List[User] = []

    # -------------------- helpers --------------------
    async def refresh_lists() -> None:
        """Reload users from the DB with a fresh session."""
        nonlocal users
        async with async_session_maker() as s:
            users = (await s.execute(select(User).order_by(User.email))).scalars().all()

    async def count_active_admins(session: AsyncSession) -> int:
        result = await session.execute(
            select(func.count())
            .select_from(User)
            .where(
                User.is_superuser == True,  # noqa: E712
                User.is_active == True,  # noqa: E712
            )
        )
        return int(result.scalar() or 0)

    # -------------------- actions --------------------
    async def create_user_action(
        email: str, plain_password: str, make_admin: bool
    ) -> None:
        email = (email or "").strip().lower()
        if not email or not plain_password:
            ui.notify("Email and password are required", color="negative")
            return
        hashed = get_password_hash(plain_password)
        async with async_session_maker() as s:
            try:
                new_user = User(
                    email=email,
                    hashed_password=hashed,
                    is_active=True,
                    is_verified=True,
                    is_superuser=make_admin,
                )
                s.add(new_user)
                await s.commit()
                ui.notify("User created", color="positive")
            except IntegrityError:
                await s.rollback()
                ui.notify("Email already exists", color="negative")
                return
        await refresh_lists()
        render_users_table.refresh()

    async def delete_user(user_id: UUID) -> None:
        if user_id == current_user.id:
            ui.notify("You cannot delete your own account.", color="negative")
            return
        async with async_session_maker() as s:
            u = await s.get(User, user_id)
            if not u:
                ui.notify("User not found", color="negative")
                return
            if (
                u.is_superuser
                and u.is_active
                and await count_active_admins(s) <= 1
            ):
                ui.notify("Cannot delete the last active admin.", color="negative")
                return
            await s.execute(
                delete(Access).where(Access.user_id == user_id)
            )  # clean dependent rows
            await s.delete(u)
            await s.commit()
        ui.notify("User deleted", color="positive")
        await refresh_lists()
        render_users_table.refresh()

    async def toggle_active(user_id: UUID) -> None:
        if user_id == current_user.id:
            ui.notify(
                "You cannot deactivate your own account.",
                color="negative",
            )
            return

        async with async_session_maker() as s:
            u = await s.get(User, user_id)
            if not u:
                ui.notify("User not found", color="negative")
                return
            if (
                u.is_active
                and u.is_superuser
                and await count_active_admins(s) <= 1
            ):
                ui.notify(
                    "Cannot deactivate the last active admin.",
                    color="negative",
                )
                return
            u.is_active = not u.is_active
            await s.commit()
        ui.notify("User status updated", color="positive")
        await refresh_lists()
        render_users_table.refresh()

    async def toggle_admin(user_id: UUID) -> None:
        if user_id == current_user.id:
            ui.notify("You cannot remove your own admin flag.", color="negative")
            return
        async with async_session_maker() as s:
            u = await s.get(User, user_id)
            if not u:
                ui.notify("User not found", color="negative")
                return
            if u.is_superuser:
                if (
                    u.is_active
                    and await count_active_admins(s) <= 1
                ):
                    ui.notify(
                        "Cannot remove admin: this is the last active admin.",
                        color="negative",
                    )
                    return
                u.is_superuser = False
            else:
                u.is_superuser = True
            await s.commit()
        ui.notify("Admin flag toggled", color="positive")
        await refresh_lists()
        render_users_table.refresh()

    # -------------------- initial data --------------------
    await refresh_lists()

    # -------------------- UI --------------------
    with ui.column().classes("m-4 gap-4 w-full"):
        # Create user
        with ui.card().classes("p-4 w-full max-w-3xl"):
            ui.label("Create user").classes("text-lg mb-2")
            email_in = ui.input(
                "email", validation={"required": lambda v: bool(v and v.strip())}
            ).classes("w-96")
            pwd_in = ui.input(
                "password (plain, will be hashed on server)", password=True
            ).classes("w-96")
            admin_ck = ui.checkbox("Make admin")
            ui.button(
                "Create",
                on_click=lambda e=email_in, p=pwd_in, a=admin_ck: create_user_action(
                    e.value or "", p.value or "", bool(a.value)
                ),
            ).classes("mt-2")

        @ui.refreshable
        def render_users_table():
            with ui.card().classes("p-4 w-full"):
                ui.label("Users").classes("text-lg mb-2")

                # Header row (only labels)
                with ui.row().classes("text-sm opacity-70 mb-1 w-full"):
                    ui.label("Email").classes("min-w-[280px]")
                    ui.label("Flags").classes("min-w-[160px]")
                    ui.label("Actions").classes("min-w-[460px]")

                # User blocks: email, flags, actions, then spacer
                for u in users:
                    with ui.column().classes("w-full"):
                        # 1) Email + flags + actions
                        flags = []
                        if u.is_active:
                            flags.append("active")
                        if getattr(u, "is_verified", False):
                            flags.append("verified")
                        if u.is_superuser:
                            flags.append("admin")

                        with ui.row().classes("items-center gap-2 mb-1 w-full"):
                            ui.label(u.email).classes("min-w-[280px] break-all")
                            ui.label(", ".join(flags) or "-").classes("min-w-[160px]")
                            with ui.row().classes("gap-2 min-w-[460px]"):
                                ui.button(
                                    "Toggle active",
                                    on_click=lambda uid=u.id: toggle_active(uid),
                                )
                                ui.button(
                                    "Toggle admin",
                                    on_click=lambda uid=u.id: toggle_admin(uid),
                                )
                                ui.button(
                                    "Delete",
                                    color="negative",
                                    on_click=lambda uid=u.id: delete_user(uid),
                                )

                        # spacer between users
                        ui.element("div").classes("h-3")

        render_users_table()
