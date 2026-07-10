# LIP demo — one-command operations.
.DEFAULT_GOAL := help

COMPOSE := docker compose

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up: ## Build and start the full stack, wait until healthy, print URLs
	$(COMPOSE) up -d --build
	@echo ""
	@echo "Waiting for the stack to become healthy..."
	@ok=0; for i in $$(seq 1 60); do \
		if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then ok=1; break; fi; \
		sleep 5; \
	done; \
	if [ $$ok = 1 ]; then \
		echo ""; \
		echo "  LIP demo is up:"; \
		echo "    UI (dispatch map):   http://localhost:3000"; \
		echo "    API docs:            http://localhost:8000/docs"; \
		echo "    Kafka UI (topics):   http://localhost:8080"; \
		echo "    Neo4j browser:       http://localhost:7474  (neo4j / lip_graph_password)"; \
		echo ""; \
		echo "  Try: make reset | make audit | make logs"; \
	else \
		echo "Stack did not become healthy in time — check 'make ps' and 'make logs'"; exit 1; \
	fi

down: ## Stop the stack (keeps data volumes)
	$(COMPOSE) down

nuke: ## Stop the stack and DELETE all data volumes (true fresh start)
	$(COMPOSE) down -v

reset: ## Demo reset: return every store, topic, and projection to the seed world
	@start=$$(date +%s); \
	$(COMPOSE) stop simulator normalizer projector >/dev/null 2>&1; \
	$(COMPOSE) exec api python -m tools.demo_reset || exit 1; \
	$(COMPOSE) start normalizer projector simulator >/dev/null 2>&1; \
	end=$$(date +%s); \
	echo ""; echo "Demo reset complete in $$((end-start))s (workers restarted)."

audit: ## Prove every event on every canonical topic conforms to envelope v1
	$(COMPOSE) exec api python -m tools.topic_audit

test: ## Run the contract unit tests inside the api container
	$(COMPOSE) exec api python -m pytest tests -q

seed-regen: ## Regenerate server/database/postgres/seed.sql from the generator
	python3 scripts/generate_seed.py

catalog: ## Regenerate EVENT-CATALOG.md from the code registry
	$(COMPOSE) exec api python -m tools.render_catalog > EVENT-CATALOG.md
	@echo "EVENT-CATALOG.md regenerated"

ps: ## Show service status
	$(COMPOSE) ps

logs: ## Tail logs from the core services
	$(COMPOSE) logs -f --tail=50 api normalizer projector simulator

tools: ## Start optional operator tools (pgAdmin on :5050)
	$(COMPOSE) --profile tools up -d pgadmin

.PHONY: help up down nuke reset audit test seed-regen catalog ps logs tools
