from __future__ import annotations

from uuid import UUID
import json
import os
from password import get_password_hash, verify_password
from nicegui import ui  # NOTE: we no longer import nicegui.app directly
from fastapi import Depends, Request, FastAPI
from fastapi_users import FastAPIUsers
from fastapi_users import models as user_models
from sqlalchemy.future import select
from typing import Optional
from datetime import datetime, timedelta
import asyncio
from functools import partial
from auth import fastapi_users, auth_backend
from contextlib import asynccontextmanager
from fastapi.responses import RedirectResponse
from db import (
    Access,
    async_session_maker,
    User,
    Score,
    get_async_session,
    ensure_admin_exists,
)
from pages import privacy_page, purchase_page  # noqa: F401
import en200_irrvbs, es200_preterite, es350_presind, fr200_presind  # noqa: F401
import admin_page  # This will auto-register the @ui.page
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


# Make /admin/users work even if the NiceGUI page is mounted at /admin
@app.get("/admin/users", include_in_schema=False)
async def admin_users_alias():
    return RedirectResponse("/admin", status_code=307)


current_user = fastapi_users.current_user()
get_optional_user = fastapi_users.current_user(optional=True)

COOKIE_NAME = auth_backend.transport.cookie_name  # "learning_lang_auth"

# --- Auth (login/logout only) routes go on the FastAPI app (not nicegui_app) ---
# Public registration is switched off: no route creates accounts. The only
# account is the administrator provisioned from ADMIN_EMAIL/ADMIN_PASSWORD.
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)


# --- lifespan: ensure admin exists ------------------------------------------
@asynccontextmanager
async def lifespan(_app):
    # ---- startup ----
    async with async_session_maker() as s:
        await ensure_admin_exists(s)
    yield


app.router.lifespan_context = lifespan

# --- content blocks ----------------------------------------------------------
resource_blocks = [
    {
        "en": "Complete guide to English irregular verbs.",
        "es": "Guía completa de los verbos irregulares en inglés.",
        "fr": "Guide complet sur les verbes irréguliers en anglais.",
        "ru": "Полное руководство по неправильным глаголам в английском.",
        "url": "https://www.spellzone.com/blog/your_complete_guide_to_irregular_verbs.htm",
    },
    {
        "en": "Full list of English irregular verbs.",
        "es": "Lista completa de los verbos irregulares en inglés.",
        "fr": "Liste complète des verbes irréguliers anglais.",
        "ru": "Полный список неправильных глаголов в английском.",
        "url": "https://wallstreetenglish.fr/fiches-anglais/grammaire/apprendre-verbes-irreguliers-en-anglais#",
    },
    {
        "en": "Table of 170 English irregular verbs with audio.",
        "es": "Tabla con 170 verbos irregulares en inglés y audio.",
        "fr": "Tableau de 170 verbes irréguliers anglais avec audio.",
        "ru": "Таблица из 170 неправильных глаголов в английском с аудио.",
        "url": "https://www.ispeakspokespoken.com/les-verbes-irreguliers-anglais/#",
    },
    {
        "en": "470+ English irregular verbs with printable PDF, flashcards, and online exercises.",
        "es": "Más de 470 verbos irregulares en inglés con PDF imprimible, tarjetas y ejercicios online.",
        "fr": "470+ verbes irréguliers anglais avec PDF imprimable, flashcards et exercices interactifs en ligne.",
        "ru": "470+ неправ. англ. глаголов с распечатываемым PDF, карточками и онлайн-упражнениями.",
        "url": "https://www.englishpage.com/irregularverbs/irregularverbs.html#",
    },
    {
        "en": "Irregular French verbs in the present tense, with tables.",
        "es": "Verbos irregulares en francés en presente, con tablas.",
        "fr": "Verbes irréguliers français au présent, avec tableaux.",
        "ru": "Неправильные французские глаголы в настоящем времени, с таблицами.",
        "url": "https://www.busuu.com/en/french/irregular-verbs#",
    },
    {
        "en": "10 common irregular French verbs.",
        "es": "10 verbos franceses frecuentes e irregulares.",
        "fr": "10 verbes français fréquents et irréguliers.",
        "ru": "10 распространённых неправильных французских глаголов.",
        "url": "https://www.lingoda.com/blog/en/irregular-verbs-french/#",
    },
    {
        "en": "Present forms of common irregular French verbs (with audio) + exercise.",
        "es": "Formas del presente de los verbos franceses irregulares comunes (con audio) + ejercicio.",
        "fr": "Formes au présent des verbes irréguliers français courants (avec audio) + exercice.",
        "ru": "Настоящее время часто используемых неправ. франц. глаголов (с аудио) + упражнение.",
        "url": "https://www.podcastfrancaisfacile.com/conjugaison/verbes-irreguliers.html#",
    },
    {
        "en": "10 essential irregular Spanish verbs.",
        "es": "10 verbos irregulares esenciales en español.",
        "fr": "10 verbes irréguliers espagnols essentiels.",
        "ru": "10 основных неправильных глаголов в испанском.",
        "url": "https://blog.rosettastone.com/common-spanish-irregular-verbs/#",
    },
    {
        "en": "Table of irregular Spanish preterite stems.",
        "es": "Tabla de raíces irregulares del pretérito en español.",
        "fr": "Tableau des radicaux irréguliers du prétérit espagnol.",
        "ru": "Таблица неправильных основ в простом прош. вр. испанского языка.",
        "url": "https://espanol.lingolia.com/en/grammar/tenses/preterito-indefinido#",
    },
    {
        "en": "Detailed guide (in English) about Spanish irregular verbs.",
        "es": "Guía detallada (en inglés) sobre los verbos irregulares del español.",
        "fr": "Guide très complet (en anglais) couvrant les verbes irréguliers espagnols.",
        "ru": "Подробное руководство (на английском) по неправильным глаголам в испанском.",
        "url": "https://preply.com/en/blog/irregular-spanish-verbs/#",
    },
    {
        "en": "Three-step game to review English past forms.",
        "es": "Juego de tres pasos para repasar los tiempos pasados en inglés.",
        "fr": "Jeu en trois étapes pour réviser les formes passées des verbes anglais.",
        "ru": "Трёхэтапная игра для повторения прошедших форм английских глаголов.",
        "url": "https://www.gamestolearnenglish.com/past-tense-game/",
    },
    {
        "en": "Progressive quizzes on 100 irregular English verbs.",
        "es": "Cuestionarios progresivos sobre 100 verbos irregulares en inglés.",
        "fr": "Quiz progressifs sur 100 verbes irréguliers anglais.",
        "ru": "Поэтапные тесты по 100 неправильным глаголам английского.",
        "url": "https://www.helpfulgames.com/subjects/english/345-irregular-verbs.html#",
    },
    {
        "en": "Several mini-games to practice English past verb forms.",
        "es": "Varios minijuegos para practicar los tiempos pasados en inglés.",
        "fr": "Plusieurs mini-jeux pour mémoriser les formes passées des verbes irréguliers anglais.",
        "ru": "Несколько мини-игр для тренировки прошедших форм английских глаголов.",
        "url": "https://www.turtlediary.com/game/irregular-verbs.html#",
    },
    {
        "en": "Online game to conjugate an irregular French verb in the present tense.",
        "es": "Juego en línea para conjugar un verbo francés irregular en presente.",
        "fr": "Jeu en ligne où l’on conjugue un verbe français irrégulier au présent.",
        "ru": "Онлайн-игра для спряжения неправильного французского глагола в наст. вр.",
        "url": "https://jeux.ieducatif.fr/jeu-educatif/jeux-cm2/conjugaison-verbes-irreguliers-present/#",
    },
    {
        "en": "Fill-in-the-blank quiz on irregular French verbs.",
        "es": "Cuestionario de huecos sobre los verbos irregulares franceses.",
        "fr": "Quiz à trous demandant de conjuguer des verbes français irréguliers.",
        "ru": "Упражнение с пропусками на неправильные французские глаголы.",
        "url": "https://www.francaisfacile.com/exercices/exercice-francais-2/exercice-francais-6154.php#",
    },
    {
        "en": "Exercises and games to practice English, Spanish and French irregular preterite verbs.",
        "es": "Ejercicios y juegos para practicar los verbos irregulares ingleses, franceses y españoles (pretérito).",
        "fr": "Exercices et jeux pour pratiquer la conjugaison des verbes irréguliers anglais, espagnols, et français au passé simple.",
        "ru": "Упражн. и игры для тренировки англ., испанск. и франц. непр. глаг. в простом прош. вр.",
        "url": "https://conjuguemos.com/verb/137#",
    },
    {
        "en": "Free mini-games to practice basic Spanish verbs.",
        "es": "Minijuegos gratuitos para practicar los verbos básicos en español.",
        "fr": "Mini-jeux interactifs gratuits pour s’entraîner sur les verbes espagnols de base.",
        "ru": "Бесплатные мини-игры для тренировки основных испанских глаголов.",
        "url": "https://www.digitaldialects.com/Spanish.htm#",
    },
    {
        "en": "Fill-in-the-blank exercise on Spanish irregular preterite verbs.",
        "es": "Ejercicio de huecos sobre los verbos irregulares en pretérito en español.",
        "fr": "Exercice en ligne à trous : conjugaison des verbes irréguliers espagnols au passé simple.",
        "ru": "Упражнение с пропусками на неправильные глаголы в простом прош. вр. (испанский).",
        "url": "https://www.123teachme.com/learn_spanish/teacher_exercises_wb1_39",
    },
    {
        "en": "Interactive task: choose the right present form of various French irregular verbs.",
        "es": "Ejercicio interactivo: elige la forma correcta en presente de varios verbos franceses irregulares.",
        "fr": "Exercice interactif : remplir la bonne forme au présent pour divers verbes français irréguliers.",
        "ru": "Интерактивное упражнение: выбрать правильную форму наст. вр. для непр. фр. глаголов.",
        "url": "https://francais.lingolia.com/fr/grammaire/les-temps/les-verbes-irreguliers/exercices#",
    },
    {
        "en": "Online quiz (in English): write the 1st person singular present form of each Spanish verb.",
        "es": "Cuestionario en línea (en inglés): escribe la forma en presente de la primera persona del singular de cada verbo en español.",
        "fr": "Quiz en ligne (en anglais) : écrire la forme de la 1ʳᵉ personne du présent pour chaque infinitif d’un verbe en espagnol.",
        "ru": "Онлайн-тест (на англ.): напишите форму наст. вр. для 1-го лица ед. ч. испанского глагола.",
        "url": "https://studyspanish.com/grammar/test/irregfirst#",
    },
]


# --- helpers & UI pages ------------------------------------------------------
def render_resource_block(resource):
    with ui.column().classes("p-2 border rounded shadow-sm bg-white max-w-xs"):
        ui.label(resource["en"]).style("font-weight: bold")
        ui.label(resource["es"])
        ui.label(resource["fr"])
        ui.label(resource["ru"])
        ui.link(
            "👉 See it on their website | Ver en su sitio web | Voir sur leur site | См. на сайте",
            resource["url"],
        ).style("color: blue")


def logout_button(text: str = "🚪 Logout") -> None:
    """Renders a button that triggers the server-side logout and reloads the page."""

    def _logout() -> None:
        ui.run_javascript(
            """
            fetch('/auth/logout', {
            method: 'POST',
            credentials: 'include'
            }).then(r => r.status === 404
                    ? fetch('/auth/jwt/logout', {method: 'POST', credentials: 'include'})
                    : r)
            .then(r => {
                if (r && r.ok) {
                window.location.href = '/';
                } else {
                alert('Logout failed.');
                }
            });
            """
        )

    ui.button(text, on_click=_logout).classes("nicegui-link text-lg")


@ui.page("/")
async def main_menu(
    request: Request, user: Optional[User] = Depends(get_optional_user)
) -> None:
    ui.add_head_html(
        """
        <style>
          .main-title { font-size: 2.5rem; font-weight: bold; text-align: center; margin-bottom: 2rem; }
          .trainer-link { width: 100%; max-width: 400px; font-size: 1.35rem; }
          .main-card { max-width: 480px; padding: 2rem; border-radius: 16px; box-shadow: 0 2px 12px #0001; }
        </style>
        """
    )
    split = len(resource_blocks) // 2
    left_blocks = resource_blocks[:split]
    right_blocks = resource_blocks[split:]

    with ui.column().classes("min-h-screen"):
        with ui.row().classes(
            "w-full max-w-[1600px] justify-center items-start gap-2 flex-nowrap"
        ):
            # Left
            with ui.column().classes(
                "w-full md:w-1/3 overflow-auto max-h-[80vh] bg-green-50 p-2 border"
            ):
                for res in left_blocks:
                    render_resource_block(res)
            # Center
            with ui.column().classes("w-1/3 items-center bg-yellow-50 border"):
                with ui.card().classes("main-card p-6"):
                    # Trainers block...
                    ui.label("🌍 Irregular Verbs Conjugation Trainers").classes(
                        "text-2xl font-bold mb-4"
                    )
                    ui.link(
                        "All four trainers are free — no registration required", "/purchase"
                    ).classes(
                        "text-red-600 text-lg mb-4"
                    )
                    with ui.column().classes("items-center mb-2"):
                        ui.link(
                            "Spanish 350 Irregular Verbs – Present Indicative",
                            "/es/presind",
                        ).classes("trainer-link nicegui-link")
                        ui.link(
                            "Spanish 200 Irregular Verbs – Preterite",
                            "/es/preterite",
                        ).classes("trainer-link nicegui-link")
                        ui.link(
                            "French 200 Irregular Verbs – Present Indicative",
                            "/fr/presind",
                        ).classes("trainer-link nicegui-link")
                        ui.link("English 200 Irregular Verbs", "/en/irrvbs").classes(
                            "trainer-link nicegui-link"
                        )
                    ui.separator().classes("my-4")
                    ui.label("Administrator only").classes("text-sm")
                    with ui.row().classes("justify-between w-full"):
                        ui.link("Login", "/login").classes("nicegui-link text-lg")
                        if user is not None:
                            logout_button()
                    ui.link("Privacy notice", "/privacy").classes("nicegui-link text-sm mt-2")
            # Right
            with ui.column().classes(
                "w-full md:w-1/3 overflow-auto max-h-[80vh] bg-blue-50 p-2 border"
            ):
                for res in right_blocks:
                    render_resource_block(res)


@ui.page("/login")
async def login_page() -> None:
    email = ui.input("Email")
    password = ui.input("Password", password=True)

    def submit() -> None:
        ui.run_javascript(
            f"""
            async function doLogin() {{
            const opts = {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                body: new URLSearchParams({json.dumps({"username": email.value, "password": password.value})}),
                credentials: 'include'
            }};
            let r = await fetch('/auth/login', opts);
            if (r.status === 404) {{
                r = await fetch('/auth/jwt/login', opts);
            }}
            if (r.ok) {{
                window.location.href = '/';
            }} else {{
                alert('Bad credentials');
            }}
            }}
            doLogin();
            """
        )

    ui.button("Login", on_click=submit)


@ui.page("/register")
async def register_page() -> None:
    ui.label("Registration is closed.").classes("text-lg")
    ui.label("All four trainers are free and need no account.")
    ui.link("Back to the trainers", "/")


# --- Bind NiceGUI to the FastAPI app (CRUCIAL for Render/Uvicorn) -------------
ui.run_with(app)


# --- Health check for Render --------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"ok": True}
