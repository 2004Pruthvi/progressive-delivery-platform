.PHONY: help install lint test run docker-build docker-run k8s-apply tf-init tf-plan tf-apply clean

PYTHON := python
PIP := pip
DOCKER := docker
APP_NAME := release-demo-app
IMAGE_NAME := $(APP_NAME)
TAG := v1.0.0
COMMIT_SHA := $(shell git rev-parse --short HEAD 2>nul || echo local)

help:
	@echo "Available commands:"
	@echo "  make install       Install application dependencies"
	@echo "  make lint          Run code formatting and lint checks"
	@echo "  make test          Run unit and integration tests"
	@echo "  make run           Run application locally with uvicorn"
	@echo "  make docker-build  Build container image"
	@echo "  make docker-run    Run container image locally on port 8000"
	@echo "  make test-load     Run traffic generator script against running app"
	@echo "  make clean         Clean temporary files and caches"

install:
	$(PIP) install -r app/requirements.txt
	$(PIP) install -r app/requirements-dev.txt

lint:
	flake8 app tests --max-line-length=120 --exclude=__pycache__
	black --check app tests

format:
	black app tests

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	$(DOCKER) build -f docker/Dockerfile -t $(IMAGE_NAME):$(TAG) -t $(IMAGE_NAME):$(COMMIT_SHA) .

docker-run:
	$(DOCKER) run --rm -p 8000:8000 --name $(APP_NAME) $(IMAGE_NAME):$(TAG)

test-load:
	$(PYTHON) scripts/traffic-generator.py --url http://localhost:8000 --duration 30 --concurrency 5

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage 2>/dev/null || true
