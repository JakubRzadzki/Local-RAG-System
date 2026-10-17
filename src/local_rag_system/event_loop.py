"""Event loop factory: psycopg's async mode cannot use Windows' default ProactorEventLoop."""

import asyncio


def selector_loop_factory() -> asyncio.AbstractEventLoop:
    """Return a ``SelectorEventLoop`` (supported by psycopg on every platform)."""
    return asyncio.SelectorEventLoop()
