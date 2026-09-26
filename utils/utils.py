# utils/auth_helpers.py
from nicegui import ui
from auth import auth_backend  # your existing backend w/ CookieTransport

COOKIE_NAME = auth_backend.transport.cookie_name  # "learning_lang_auth"


def logout_button(text: str = "🚪 Logout") -> None:
    """Render a button that wipes the auth cookie client-side, then reloads 🔄"""

    def _logout() -> None:
        ui.run_javascript(  #  ← you forgot to execute the JS!
            f"document.cookie='{COOKIE_NAME}=; Max-Age=0; path=/';"
            "window.location.href='/'"
        )

    ui.button(text, on_click=_logout).classes("nicegui-link text-lg")
