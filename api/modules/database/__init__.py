from .session import Base, engine, get_db, SessionLocal
from .models import User, Project

# Création des tables si elles n'existent pas
Base.metadata.create_all(bind=engine)
