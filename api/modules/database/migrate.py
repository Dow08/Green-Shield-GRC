"""migrate.py — script de migration JSON → SQLite (RETIRÉ le 01/08/2026).

Le modèle SQLAlchemy `Project` a été supprimé lors de l'audit de sécurité :
les missions restent en fichiers JSON (cohérent avec le fonctionnement
hors-ligne et la portabilité par archive chiffrée). Seul le modèle `User`
subsiste en SQLite pour l'authentification.

Ce fichier est conservé vide pour ne pas casser d'éventuels imports
résiduels, mais ne fait plus rien.
"""

