"""Run database migrations."""
import os
import sys
import time

import psycopg2
from alembic import command
from alembic.config import Config

from ai_assistant.config import settings


def wait_for_db(max_retries=30, delay=1):
    """Wait for database to be available."""
    retries = 0
    while retries < max_retries:
        try:
            conn = psycopg2.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
            )
            conn.close()
            print("✓ Database is ready!")
            return True
        except psycopg2.OperationalError:
            retries += 1
            print(f"Waiting for database... ({retries}/{max_retries})")
            time.sleep(delay)
    
    print("✗ Could not connect to database")
    return False


def run_migrations():
    """Run Alembic migrations."""
    print("Running database migrations...")
    
    # Get the directory containing alembic.ini
    alembic_dir = os.path.dirname(__file__)
    alembic_ini_path = os.path.join(alembic_dir, "alembic.ini")
    
    # Create Alembic config
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}",
    )
    
    try:
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        print("✓ Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False


if __name__ == "__main__":
    if not wait_for_db():
        sys.exit(1)
    
    if not run_migrations():
        sys.exit(1)
    
    print("✓ Database setup complete!")

