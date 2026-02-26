from logging.config import fileConfig
import os
import sys

from alembic import context
from sqlalchemy import create_engine, pool

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.core.config import settings
from app.core.database import Base
from app.models.user import User
from app.models.chat import ChatHistory

config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online():
    engine = create_engine(
        settings["DATABASE_URL"],
        poolclass=pool.NullPool,
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()