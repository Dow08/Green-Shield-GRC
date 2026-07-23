# ------------------------------------------------------------------
# Target_Lab — la CIBLE d'audit (hôte Linux minimaliste)
# ------------------------------------------------------------------
# Ce conteneur "représente" un serveur audité. Ses fichiers de
# configuration vulnérables sont montés en volume (voir docker-compose).
# Il ne fait rien d'autre que rester vivant : AUCUN service réseau exposé.
FROM debian:stable-slim

LABEL role="target" project="AuditCraft-GRC"

# Emplacements standards où résideront les configs montées.
RUN mkdir -p /etc/ssh /etc/nginx

# La cible reste simplement en vie ; l'auditeur lit ses fichiers (read-only).
CMD ["sleep", "infinity"]
