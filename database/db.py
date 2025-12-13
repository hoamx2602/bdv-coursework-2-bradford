# database/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

# Load .env once, globally
load_dotenv()

def get_engine() -> Engine:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

    connect_args = {}
    sslmode = os.getenv("PGSSLMODE")
    if sslmode:
        connect_args["sslmode"] = sslmode

    return create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
