import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..data_paths import resolve_data_root

# On place la DB dans le dossier de données de l'application
DB_DIR = str(resolve_data_root())
os.makedirs(DB_DIR, exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'greenshield.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
