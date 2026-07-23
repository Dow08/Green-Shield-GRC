# ==================================================================
# GREEN SHIELD — déploiement Zero-Friction
# ==================================================================
DC := $(shell command -v docker-compose >/dev/null 2>&1 && echo docker-compose || echo "docker compose")
URL := http://localhost:8080

.DEFAULT_GOAL := help
.PHONY: help up down restart logs ps clean

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

up: ## Construit et démarre la plateforme
	$(DC) up --build -d
	@echo ""
	@echo "  ✅ GREEN SHIELD est lancé  ->  $(URL)"
	@echo ""

down: ## Arrête les conteneurs
	$(DC) down

restart: ## Redémarre proprement
	$(DC) down && $(DC) up --build -d
	@echo "  ✅ Redémarré  ->  $(URL)"

logs: ## Suit les logs
	$(DC) logs -f

ps: ## État des conteneurs
	$(DC) ps

clean: ## Arrête tout et supprime volumes + images du projet
	$(DC) down -v --rmi local --remove-orphans
	@echo "  🧹 Environnement nettoyé."
