import logging
import os
import time
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from ..data_paths import resolve_data_root

logger = logging.getLogger(__name__)

# Nombre de connexions simultanément empruntées au-delà duquel on trace. Le
# `QueuePool ... timed out` n'arrive qu'une fois le pool à sec : sans signal
# précurseur, il ne reste qu'une trace qui désigne la victime (la requête qui
# attendait) et jamais le coupable (ce qui retenait les connexions).
SEUIL_ALERTE_POOL = 15

# On place la DB dans le dossier de données de l'application
DB_DIR = str(resolve_data_root())
os.makedirs(DB_DIR, exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'greenshield.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False},
    # Filet de sécurité (08/09/2026) : le défaut (5 + 10 en débordement) s'est
    # révélé insuffisant face à une fuite de sessions non refermées
    # (`crud.py::_resolve_test_deps`) — un pool plus large limite la casse si
    # une fuite similaire réapparaît, sans coût réel ici (SQLite local, une
    # seule instance).
    #
    # 09/09/2026 : la fuite est désormais traitée à la source. Le correctif
    # précédent reposait sur `atexit.register(db.close)`, qui ne referme qu'à
    # l'arrêt du processus — chaque appel retenait donc sa connexion pendant
    # toute la vie du serveur. `_resolve_test_deps` prête maintenant une
    # session unique remise à zéro, au lieu d'en créer une par appel.
    pool_size=10, max_overflow=20,
    # 30 s (le défaut) fige l'interface une demi-minute avant de renvoyer une
    # erreur : l'utilisateur croit l'application plantée. Sur une base SQLite
    # locale, ne pas obtenir de connexion en 5 s ne traduit jamais une
    # contention normale mais une fuite — autant échouer vite et le voir.
    pool_timeout=5,
)


# Délai minimal entre deux alertes de tension. Révision d'audit (09/09/2026) :
# sans lui, l'écouteur émettait une ligne par emprunt au-delà du seuil — sous
# saturation, des centaines de lignes identiques par minute. Une alerte noyée
# dans son propre bruit est une alerte qu'on apprend à ignorer.
DELAI_ALERTE_POOL_S = 30.0
_derniere_alerte_pool = 0.0


@event.listens_for(engine, "checkout")
def _tracer_tension_pool(_dbapi_connection, _record, _proxy) -> None:
    """Alerte quand le pool approche de la saturation, avant la panne."""
    global _derniere_alerte_pool
    empruntees = engine.pool.checkedout()
    if empruntees < SEUIL_ALERTE_POOL:
        return
    maintenant = time.monotonic()
    if maintenant - _derniere_alerte_pool < DELAI_ALERTE_POOL_S:
        return
    _derniere_alerte_pool = maintenant
    logger.warning(
        "Pool de connexions sous tension : %d empruntées (seuil %d) — %s",
        empruntees, SEUIL_ALERTE_POOL, engine.pool.status(),
    )

# SQLite par défaut (journal_mode=delete) verrouille toute la base pendant une
# écriture : sous FastAPI, plusieurs requêtes concurrentes (ex. chargement du
# tableau de bord qui interroge projets + référentiels + échéances RGPD en
# parallèle) se bloquent alors mutuellement, avec des lenteurs de plusieurs
# secondes voire des "database is locked" remontées en 500. Le mode WAL laisse
# les lecteurs continuer pendant une écriture ; busy_timeout fait attendre une
# connexion plutôt que d'échouer immédiatement en cas de verrou bref restant.
@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_connection, _record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=10000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
