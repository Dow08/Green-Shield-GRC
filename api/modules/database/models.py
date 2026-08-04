from sqlalchemy import Column, String, Integer, JSON, Boolean, ForeignKey
from .session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")  # user, admin
    license_key = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)


# NOTE AUDIT 01/08/2026 : le modèle Project assure le lien de propriété
# (owner_id) entre un utilisateur et ses missions. L'état complet de la
# mission reste dans les fichiers JSON (cohérent avec le fonctionnement
# hors-ligne et la portabilité par archive chiffrée). Les colonnes JSON
# ici ne servent qu'au listing rapide sans relire chaque fichier.
class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    client = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, default="en_cours")
    progress = Column(Integer, default=0)
    created_at = Column(String)
    updated_at = Column(String)
    steps = Column(JSON, default=dict)
    grc = Column(JSON, default=dict)
    technical_findings = Column(JSON, default=dict)
    socle = Column(JSON, default=dict)
    framework_id = Column(String, default="iso27001")
    framework_ids = Column(JSON, default=list)
    is_demo = Column(String, nullable=True)

    def to_dict(self):
        """Reconstitue le dictionnaire attendu par le reste du code."""
        d = {
            "id": self.id,
            "name": self.name,
            "client": self.client,
            "type": self.type,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "steps": self.steps or {},
            "grc": self.grc or {},
            "technical_findings": self.technical_findings or {},
            "socle": self.socle or {},
            "framework_id": self.framework_id,
            "framework_ids": self.framework_ids or [self.framework_id],
        }
        if self.is_demo:
            d["is_demo"] = self.is_demo
        return d

