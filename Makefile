SHELL := /bin/zsh

ENV_FILE := .env
ENV_EXAMPLE := .env-example
ENV_EXAMPLE_FALLBACK := .env.example

-include $(ENV_FILE)
export

PYTHON_BIN ?= python3.13
VENV := .venv
CLI := $(VENV)/bin/apple-agent-kit

MODEL ?=
PLATFORM ?=
REPO ?=
ARGS ?=

.PHONY: \
	all \
	env \
	check-python \
	check-uv \
	install \
	lock \
	doctor \
	models \
	download \
	prepare \
	prepare-all \
	inspect \
	login \
	publish \
	clean \
	clean-cache \
	clean-artifacts

all: env check-python check-uv install doctor

env:
	@if [ -f "$(ENV_FILE)" ]; then \
		echo "[OK] $(ENV_FILE) already exists"; \
	elif [ -f "$(ENV_EXAMPLE)" ]; then \
		cp "$(ENV_EXAMPLE)" "$(ENV_FILE)"; \
		echo "[OK] Created $(ENV_FILE) from $(ENV_EXAMPLE)"; \
	elif [ -f "$(ENV_EXAMPLE_FALLBACK)" ]; then \
		cp "$(ENV_EXAMPLE_FALLBACK)" "$(ENV_FILE)"; \
		echo "[OK] Created $(ENV_FILE) from $(ENV_EXAMPLE_FALLBACK)"; \
	else \
		echo "[ERROR] No environment example file was found"; \
		exit 1; \
	fi

check-python:
	@test -n "$(PYTHON_BIN)" || (echo "[ERROR] PYTHON_BIN is not configured"; exit 1)
	@test -x "$(PYTHON_BIN)" || command -v "$(PYTHON_BIN)" >/dev/null 2>&1 || (echo "[ERROR] Python executable not found: $(PYTHON_BIN)"; exit 1)
	@echo "[OK] Python: $(PYTHON_BIN)"
	@"$(PYTHON_BIN)" --version

check-uv:
	@command -v uv >/dev/null 2>&1 || (echo "[ERROR] uv was not found. Install it with: brew install uv"; exit 1)
	@echo "[OK] uv: $$(command -v uv)"
	@uv --version

install:
	@echo "[INFO] Synchronizing AppleAgentKitPython environment..."
	uv sync --python "$(PYTHON_BIN)"
	@echo "[OK] Environment synchronized"

lock:
	uv lock

doctor:
	@echo "[INFO] Validating environment..."
	$(CLI) doctor

models:
	$(CLI) models $(if $(PLATFORM),--platform $(PLATFORM),) $(ARGS)

download:
	$(CLI) download $(MODEL) $(if $(PLATFORM),--platform $(PLATFORM),) $(ARGS)

prepare:
	$(CLI) prepare $(MODEL) $(if $(PLATFORM),--platform $(PLATFORM),) $(ARGS)

prepare-all:
	$(CLI) prepare-all $(MODEL) $(ARGS)

inspect:
	$(CLI) inspect $(MODEL) $(if $(PLATFORM),--platform $(PLATFORM),) $(ARGS)

login:
	$(CLI) login

publish:
	@test -n "$(REPO)" || (echo "[ERROR] REPO is required. Example: make publish REPO=SoreGus/Qwen3-1.7B-CoreAI"; exit 1)
	$(CLI) publish $(MODEL) --repo "$(REPO)" $(ARGS)

clean:
	rm -rf "$(VENV)"
	rm -rf build
	rm -rf dist
	find . -name "*.egg-info" -type d -prune -exec rm -rf {} +
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete
	@echo "[OK] Development environment cleaned"

clean-cache:
	rm -rf "$${APPLE_AGENT_KIT_CACHE_DIR:-.cache}"
	@echo "[OK] Cache cleaned"

clean-artifacts:
	rm -rf "$${APPLE_AGENT_KIT_ARTIFACTS_DIR:-Artifacts}"
	@echo "[OK] Artifacts cleaned"
