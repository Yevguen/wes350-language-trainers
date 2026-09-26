from __future__ import annotations
import os
from pathlib import Path
import asyncio
import uuid
from typing import AsyncGenerator, List
from dotenv import load_dotenv
from sqlalchemy import select, func
from datetime import datetime, timezone
from password import get_password_hash, verify_password

load_dotenv()
# ─── Core SQLAlchemy imports ─────────────────────────────────────────────────
from sqlalchemy import (
    Boolean,
    String,
    Column,
    Integer,
    ForeignKey,
    DateTime,
)

# ─── Async support ───────────────────────────────────────────────────────────
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,  # ← session factory for AsyncSession
    AsyncSession,  # ← used in Depends(get_async_session)
)
from sqlalchemy.orm import (
    DeclarativeBase,  # ← you can also use "Base = declarative_base()" in 1.x style
    Mapped,
    mapped_column,
    relationship,
)

# ─── (Optional) FastAPI/SQLAlchemy‐Users integration ─────────────────────────
from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase, GUID

# ───────────────────────────────────────────────────────────────────────────────

# Now you can define engine, sessionmaker, Base, and your models below:

BASE_DIR = Path(__file__).parent.resolve()  # e.g. C:\WES350
DATABASE_FILE = BASE_DIR / "test.db"  # e.g. C:\WES350\test.db
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite+aiosqlite:///{DATABASE_FILE}"

# --- engine & session factory (one place only) ---
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args={"ssl": True} if DATABASE_URL.startswith("postgresql+asyncpg") else {},
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Dependency for FastAPI
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:  # ← use the factory name
        yield session


# 2. Declarative Base
class Base(DeclarativeBase):
    pass


# 3.1 User model
class User(Base):
    __tablename__ = "user"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    scores: Mapped[List["Score"]] = relationship(
        back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )


# 3.2 Quiz model
class Quiz(Base):
    __tablename__ = "quiz"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)

    scores: Mapped[List["Score"]] = relationship(
        back_populates="quiz", lazy="selectin", cascade="all, delete-orphan"
    )


# 3.3 Score model
class Score(Base):
    __tablename__ = "score"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("user.id"))
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quiz.id"))
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    taken_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),  # <— fix
        nullable=False,
    )
    user: Mapped[User] = relationship(back_populates="scores", lazy="joined")
    quiz: Mapped[Quiz] = relationship(back_populates="scores", lazy="joined")


# 3.4 Access model
class Access(Base):
    __tablename__ = "access"
    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("user.id"), nullable=False, index=True
    )
    plan: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# 5. FastAPI Users - User DB provider
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


# 6. Create all tables
async def create_all_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


async def ensure_admin_exists(session: AsyncSession) -> None:
    # normalize inputs
    admin_email = (ADMIN_EMAIL or "").strip().lower()
    admin_pwd = (ADMIN_PASSWORD or "").strip()
    if not admin_email or not admin_pwd:
        return

    res = await session.execute(
        select(User).where(func.lower(User.email) == admin_email)
    )
    user = res.scalar_one_or_none()

    if user:
        # update hash only if the configured password doesn't match
        if not verify_password(admin_pwd, user.hashed_password):
            user.hashed_password = get_password_hash(admin_pwd)
        # enforce flags
        user.is_active = True
        user.is_superuser = True
        user.is_verified = True
    else:
        session.add(
            User(
                email=admin_email,
                hashed_password=get_password_hash(admin_pwd),
                is_active=True,
                is_superuser=True,
                is_verified=True,
            )
        )

    await session.commit()


if __name__ == "__main__":
    asyncio.run(create_all_tables())
