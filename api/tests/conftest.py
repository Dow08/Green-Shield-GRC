import sys
from pathlib import Path

# Ajouter api au sys.path pour les tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
import main
from modules import auth

@pytest.fixture(autouse=True)
def override_dependency():
    main.app.dependency_overrides[auth.verify_token] = auth.override_auth
    yield
    main.app.dependency_overrides.clear()
