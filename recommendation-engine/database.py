"""
Database — Async PostgreSQL connection pool via psycopg3.
Connects to the same Neon PostgreSQL instance as the Node.js backend.
"""

import sys
import asyncio

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://user:pass@localhost/vanisetu"
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "development"
    backend_url: str = "http://localhost:3001"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Global connection pool — initialized at startup
_pool: AsyncConnectionPool | None = None


async def init_pool():
    """Create the connection pool. Called once at FastAPI startup."""
    global _pool
    _pool = AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=2,
        max_size=10,
        open=False,
        kwargs={"row_factory": dict_row},
    )
    await _pool.open()
    return _pool


async def close_pool():
    """Gracefully close the pool. Called at FastAPI shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> AsyncConnectionPool:
    """Get the active connection pool."""
    if _pool is None or getattr(_pool, "closed", False):
        raise RuntimeError("Database pool not initialized or connection failed. Please ensure DATABASE_URL is set in .env.")
    return _pool


@asynccontextmanager
async def get_connection(timeout: float = 3.0):
    """Async context manager for a single connection from the pool."""
    pool = get_pool()
    async with pool.connection(timeout=timeout) as conn:
        yield conn
