from uuid import UUID
from fastapi import Depends
from fastapi_users import FastAPIUsers, BaseUserManager, UUIDIDMixin
from fastapi_users.authentication import (
    CookieTransport,
    JWTStrategy,
    AuthenticationBackend,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from password import verify_password as _verify, get_password_hash as _hash
from db import User, get_async_session

import os
from dotenv import load_dotenv

load_dotenv()

SECRET = os.getenv("SECRET")

if not SECRET:
    raise RuntimeError("SECRET environment variable is required")

COOKIE_LIFETIME = 14 * 24 * 3600  # 14 days


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    # use centralized wrappers (argon2 + bcrypt)
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return _verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return _hash(password)

    async def on_after_register(self, user: User, request=None):
        user.is_verified = True
        await self.user_db.update(user)


async def get_user_db(session=Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


cookie_transport = CookieTransport(
    cookie_name="learning_lang_auth",
    cookie_max_age=COOKIE_LIFETIME,
    cookie_secure=True,
    cookie_samesite="lax",
)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=COOKIE_LIFETIME)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, UUID](get_user_manager, [auth_backend])
