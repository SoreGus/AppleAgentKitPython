SHELL := /bin/zsh

ENV_FILE := .env

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

PYTHON_BIN ?= python3.13
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(PYTHON) -m pip
CLI := $(VENV)/bin/apple-agent-kit

.PHONY: all setup install doctor models prepare clean clean-cache clean-artifacts

all: setup install doctor

setup:
	@test -n "$(PYTHON_BIN)"
	$(PYTHON_BIN) -m venv $(VENV)

install:
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e .

doctor:
	$(CLI) doctor

models:
	$(CLI) models

prepare:
	$(CLI) prepare

clean:
	rm -rf $(VENV)
	rm -rf build
	rm -rf dist
	find . -name "*.egg-info" -type d -prune -exec rm -rf {} +

clean-cache:
	rm -rf $${APPLE_AGENT_KIT_CACHE_DIR:-.cache}

clean-artifacts:
	rm -rf $${APPLE_AGENT_KIT_ARTIFACTS_DIR:-Artifacts}
