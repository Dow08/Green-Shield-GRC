import os
import sys
import tempfile
from pathlib import Path

# Ajouter api au sys.path pour les tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# Isolation des données de test — À FAIRE AVANT TOUT IMPORT DE `main`.
#
# `modules/database/session.py` résout l'emplacement de la base **au moment de
# l'import** (`DB_DIR = str(resolve_data_root())`). Sans cette redirection, le
# moteur SQLAlchemy des tests pointait sur la base réelle de l'utilisateur
# (`%APPDATA%\GreenShield\greenshield.db`) — et le `drop_all()` de la fixture
# ci-dessous **effaçait tous ses comptes à chaque exécution de la suite**.
# Constaté le 31/07/2026 : impossible de se reconnecter après un `pytest`.
#
# `resolve_data_root()` étant le parent de `resolve_projects_dir()`, on pointe
# l'override sur un sous-dossier `projects` d'un répertoire temporaire dédié.
# ---------------------------------------------------------------------------
_RACINE_TESTS = Path(tempfile.gettempdir()) / "greenshield-tests"
os.environ["GREENSHIELD_DATA_DIR"] = str(_RACINE_TESTS / "projects")
(_RACINE_TESTS / "projects").mkdir(parents=True, exist_ok=True)

import pytest
from fastapi.testclient import TestClient
import main
from modules import auth
from modules.database.models import User


def _mock_current_user():
    """Utilisateur factice pour les tests — contourne l'authentification JWT
    sans laisser de trou exploitable en production (l'ancienne `verify_token`
    était un no-op qui ne retournait rien, celui-ci retourne un User valide)."""
    return User(id=0, email="test@test.local", password_hash="", role="user", is_premium=False)


@pytest.fixture(autouse=True)
def override_dependency():
    from modules.database.models import Base
    from modules.database.session import engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    main.app.dependency_overrides[auth.get_current_user] = _mock_current_user
    yield
    main.app.dependency_overrides.clear()
    engine.dispose()

import patch_deps
from modules.projects import crud, snapshots_routes
from modules import collecte_technique, copilot_grc

patch_deps.patch_module_functions(crud)
patch_deps.patch_module_functions(snapshots_routes)
patch_deps.patch_module_functions(collecte_technique)
patch_deps.patch_module_functions(copilot_grc)

