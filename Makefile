SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -O extglob -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules
BUMP_FLAGS := --allow-dirty --no-commit --no-tag

.DEFAULT_GOAL := help
ENVIRONMENT := build
VERSION := $(shell pyproject-info project.version | sed 's/"//g')
COMMIT_HASH := $(shell git log -1 --pretty=format:"sha-%h")
RULES_FILE := ~/python.cursorrules
GITHUB_REGISTRY := ghcr.io
REGISTRY_REPO_ROOT := woeplanet
DOCKER_BUILDER := woeplanet-builder
PLATFORMS := "linux/arm64/v8,linux/amd64"
# PLATFORMS := "linux/amd64"
DOCKER_PROGRESS := auto
# DOCKER_PROGRESS := plain
BUILD_FLAGS ?=
HADOLINT_IMAGE := hadolint/hadolint:${HADOLINT_RELEASE}

FRONTEND_DIR := ./frontend
STATIC_DIR := ./static

SPELUNKER := woeplanet-spelunker
SPELUNKER_REPO := $(REGISTRY_REPO_ROOT)/$(SPELUNKER)
SPELUNKER_IMAGE := $(SPELUNKER_REPO)
SPELUNKER_DOCKERFILE := docker/$(SPELUNKER)/Dockerfile

.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' Makefile

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
lint: format check typing yamllint docker	## Run all linters on the code base

.PHONY: format
format:	## Prettify/format the code base
	uv run ruff format src tests

.PHONY: check
check:	## Run the linter on the code base
	uv run ruff check src tests

.PHONY: typing
typing:	## Statically type check the code base
	uv run mypy src tests

.PHONY: yamllint
yamllint:	## Run yamllint
	uv run yamllint config

.PHONY: docker
docker:	## Run hadolint on the Dockerfile
	docker run --rm -i -e HADOLINT_IGNORE=DL3008 $(HADOLINT_IMAGE) < $(SPELUNKER_DOCKERFILE)

BUILD_TARGETS := build-spelunker

.PHONY: build
build: $(BUILD_TARGETS) ## Build all images

REBUILD_TARGETS := rebuild-spelunker

.PHONY: rebuild
rebuild: $(REBUILD_TARGETS) ## Rebuild all images (no cache)

RELEASE_TARGETS := release-spelunker

.PHONY: release
release: $(RELEASE_TARGETS)	## Tag and push all images

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

.PHONY: tests
tests:	## Run tests
	uv run pytest

.PHONY: test-verbose
test-verbose:	## Run tests with verbose output
	uv run pytest -v

.PHONY: coverage
coverage:	## Run tests with coverage
	uv run pytest --cov=src --cov-report=term-missing

.PHONY: serve
serve:	## Serve the application
	uvicorn woeplanet.spelunker.server:app --host $(shell hostname) --port 8080 --workers 1 --log-level debug --log-config ./config/logging.yml

build-spelunker: frontend ## Build the spelunker image
	$(MAKE) _build-image \
		-e BUILD_DOCKERFILE=./docker/$(SPELUNKER)/Dockerfile \
		-e BUILD_REPO=$(SPELUNKER_REPO) \
		-e BUILD_IMAGE=$(SPELUNKER_IMAGE) \
		-e BUILD_FLAGS="--build-arg VERSION=${VERSION}"

rebuild-spelunker: clean-frontend frontend	## Rebuild the spelunker image (no cache)
	$(MAKE) _build-image \
		-e BUILD_DOCKERFILE=./docker/$(SPELUNKER)/Dockerfile \
		-e BUILD_REPO=$(SPELUNKER_REPO) \
		-e BUILD_IMAGE=$(SPELUNKER_IMAGE) \
		-e BUILD_FLAGS="--no-cache --build-arg VERSION=${VERSION}"

release-spelunker: build-spelunker	## Tag and push spelunker image
	$(MAKE) _tag-image \
		-e BUILD_IMAGE=$(SPELUNKER_REPO) \
		-e BUILD_TAG=$(COMMIT_HASH)
	$(MAKE) _tag-image \
		-e BUILD_IMAGE=$(SPELUNKER_REPO) \
		-e BUILD_TAG=$(VERSION)

.PHONY: _init-builder
init_builder:
	docker buildx inspect $(DOCKER_BUILDER) > /dev/null 2>&1 || \
		docker buildx create --name $(DOCKER_BUILDER) --bootstrap --use

.PHONY: _build-image
_build-image: repo-login _init-builder
	docker buildx build --platform=$(PLATFORMS) \
		--file ${BUILD_DOCKERFILE} \
		--push \
		--tag ${GITHUB_REGISTRY}/${BUILD_IMAGE}:latest \
		--provenance=false \
		--progress=${DOCKER_PROGRESS} \
		--ssh default \
		--build-arg VERSION=${VERSION} \
		--build-arg DEBIAN_RELEASE=${DEBIAN_RELEASE} \
		${BUILD_FLAGS} .

.PHONY: _tag-image
_tag-image: repo-login
	docker buildx imagetools create ${GITHUB_REGISTRY}/$(BUILD_IMAGE):latest \
		--tag ${GITHUB_REGISTRY}/$(BUILD_IMAGE):$(BUILD_TAG)

.PHONY: repo-login
repo-login:	## Login to the container registry
	echo ${GITHUB_TOKEN} | docker login ghcr.io -u ${GITHUB_USER} --password-stdin
