# ==================================================================
# AuditCraft GRC — déploiement Zero-Friction
# ==================================================================
# Compatible « docker compose » (v2) et « docker-compose » (v1).
DC := $(shell command -v docker-compose >/dev/null 2>&1 && echo docker-compose || echo "docker compose")
URL := http://localhost:8501

.DEFAULT_GOAL := help
.PHONY: help up down clean logs restart ps

help: ## Affiche cette aide
	@echo "AuditCraft GRC — commandes disponibles :"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

up: ## Construit et démarre la plateforme, puis affiche l'URL
	$(DC) up --build -d
	@echo ""
	@echo "  ✅ AuditCraft GRC est lancé  ->  $(URL)"
	@echo ""

down: ## Arrête les conteneurs
	$(DC) down

restart: ## Redémarre proprement
	$(DC) down
	$(DC) up --build -d
	@echo "  ✅ Redémarré  ->  $(URL)"

logs: ## Suit les logs de l'auditeur
	$(DC) logs -f auditor_app

ps: ## État des conteneurs
	$(DC) ps

clean: ## Arrête tout et supprime volumes + images du projet
	$(DC) down -v --rmi local --remove-orphans
	@echo "  🧹 Environnement nettoyé."
