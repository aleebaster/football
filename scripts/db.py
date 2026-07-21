"""Database management script.

Provides CLI commands for database operations.
"""

import asyncio
import sys


async def init_db() -> None:
    """Initialize database and create tables."""
    from app.database.session import db_manager

    await db_manager.connect()
    await db_manager.create_tables()
    print("Database initialized successfully")
    await db_manager.disconnect()


async def reset_db() -> None:
    """Reset database by dropping and recreating all tables."""
    from app.database.base import Base
    from app.database.session import db_manager

    await db_manager.connect()
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database reset successfully")
    await db_manager.disconnect()


def main() -> None:
    """Main entry point for database management."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/db.py <command>")
        print("Commands: init, reset")
        sys.exit(1)

    command = sys.argv[1]
    commands = {
        "init": init_db,
        "reset": reset_db,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(commands.keys())}")
        sys.exit(1)

    asyncio.run(commands[command]())


if __name__ == "__main__":
    main()
