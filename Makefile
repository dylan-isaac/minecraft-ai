.PHONY: install run shell-completion validate lint test clean docker-build docker-up docker-down docker-shell sync-configs logs setup install-completion rules

# Local development commands (primarily for direct host machine use)
# Note: When using Dev Containers, dependencies are already installed
install:
	uv sync && uv pip install -e .

run:
	pat run --reload

shell-completion:
	pat install-completion

validate:
	pat validate

# Code quality commands - note: dependencies are already installed in the container
# If running locally outside the container, these will install dependencies first
lint:
	pat lint

test:
	pat test

clean:
	rm -rf .venv dist build *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Docker workflow commands
docker-build:
	docker compose build

docker-up:
	docker compose up minecraft-ai-dev

docker-down:
	docker compose down

# Enter container shell
docker-shell:
	docker compose exec minecraft-ai-dev zsh

# Configuration management
# Use this when you:
# 1. Add/change CLI commands in src/minecraft_ai/cli.py (updates VS Code tasks)
# 2. Update development tool versions in pyproject.toml (syncs pre-commit hooks)
sync-configs:
	if [ -f "/.dockerenv" ]; then \
		uv pip install --system pyyaml tomli; \
	fi
	python scripts/tasks/update_configs.py

# View logs for the development container
logs:
	docker compose logs -f minecraft-ai-dev

# Complete setup command (for new developers, primarily outside Dev Containers)
setup: install docker-build shell-completion validate
	@echo "Setup complete! 🚀"
	@echo "Run 'make dev' to start local development (outside container)"
	@echo "Run 'make docker-up' to start in Docker (or use Dev Containers)"

install-completion:
	@echo "Installing shell completion..."
	@python -m $(PROJECT_NAME).cli install-completion

rules:
	@echo "Processing temporary rule files..."
	@if [ -f scripts/tasks/move_rules.sh ]; then \
		chmod +x scripts/tasks/move_rules.sh && ./scripts/tasks/move_rules.sh; \
	else \
		echo "Error: scripts/tasks/move_rules.sh not found."; exit 1; \
	fi

# Add more tasks as needed
