SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -O extglob -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules
BUMP_FLAGS := --allow-dirty --no-commit --no-tag

.DEFAULT_GOAL := help
ENVIRONMENT := build
REFDATA_ENVIRONMENT := beta
VERSION := $(shell pyproject-info project.version | sed 's/"//g')
COMMIT_HASH := $(shell git log -1 --pretty=format:"sha-%h")
ECR_REPO_ROOT := kamma
PLATFORMS := "linux/arm64/v8,linux/amd64"
DOCKER_PROGRESS := auto
# DOCKER_PROGRESS := plain
RULES_FILE := ~/python.cursorrules
BUILD_FLAGS ?=

FRONTEND_DIR := ./frontend
STATIC_DIR := ./static

.PHONY: setup
setup: rules dependencies dotenv	## Setup the build environment

.PHONY: rules
rules:	## Setup local Cursor rules file
	[[ -f $(RULES_FILE) ]] && ln -sf $(RULES_FILE) .cursorrules || true

.PHONY: dependencies
dependencies:	## Install build dependencies
	uv sync --dev
	(cd $(FRONTEND_DIR) && yarn install)

.PHONY: dotenv
dotenv: .env	## Setup build secrets in .env files

.env: .environments .releases .env.template
	[[ -f .env ]] && rm -f .env
	cat .environments .releases .env.template | op inject --file-mode 0644 --force --out-file $@

.PHONY: clean-pycache
clean-pycache:	## Clean up __pycache__ files
	-find src -name '__pycache__' | xargs rm -r

.PHONY: clean-cache
clean-cache:	## Clean up tool cache directories
	-rm -rf .mypy_cache .pytest_cache .ruff_cache

.PHONY: clean-frontend
clean-frontend:	## Clean frontend build artifacts
	(cd $(FRONTEND_DIR) && yarn clean)

.PHONY: clean
clean: clean-pycache clean-cache clean-frontend	## Clean up the build environment

.PHONY: lint
lint: format check typing yamllint	## Run all linters on the code base

.PHONY: format
format:	## Prettify/format the code base
	uv run ruff format src

.PHONY: check
check:	## Run the linter on the code base
	uv run ruff check src

.PHONY: typing
typing:	## Statically type check the code base
	uv run mypy src

.PHONY: yamllint
yamllint:	## Run yamllint
	uv run yamllint config

.PHONY: frontend
frontend:	## Build the frontend assets
	(cd $(FRONTEND_DIR) && yarn build)

.PHONY: frontend-js
frontend-js:	## Build the frontend JS only
	(cd $(FRONTEND_DIR) && yarn build:js)

.PHONY: frontend-css
frontend-css:	## Build the frontend CSS only
	(cd $(FRONTEND_DIR) && yarn build:css)

.PHONY: frontend-assets
frontend-assets:	## Copy frontend assets (leaflet images, geojson)
	(cd $(FRONTEND_DIR) && yarn build:assets)

.PHONY: frontend-watch
frontend-watch:	## Watch frontend SCSS for changes
	(cd $(FRONTEND_DIR) && yarn watch:css)

.PHONY: serve
serve:	## Serve the application
	uvicorn woeplanet.spelunker.server:app --host $(shell hostname) --port 8080 --workers 1 --log-level debug --log-config ./config/logging.yml
