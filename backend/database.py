import os
import pathlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

env_path = pathlib.Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./tour.db"

if DATABASE_URL.startswith("sqlite:///"):
    sqlite_path = DATABASE_URL[len("sqlite:///"):]
    if not os.path.isabs(sqlite_path):
        sqlite_file = pathlib.Path(__file__).resolve().parent / sqlite_path
        DATABASE_URL = f"sqlite:///{sqlite_file.as_posix()}"

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
