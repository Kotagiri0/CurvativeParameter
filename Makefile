.PHONY: help test lint format clean docker-build docker-up docker-down migrate

help:
	@echo "Available commands:"
	@echo "  make test          - Run all tests"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make lint          - Run all linters"
	@echo "  make format        - Format code with black and isort"
	@echo "  make clean         - Clean Python cache files"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make migrate       - Run Django migrations"
	@echo "  make superuser     - Create Django superuser"

test:
	python manage.py test --verbosity=2

test-coverage:
	coverage run --source='.' manage.py test
	coverage report -m
	coverage html
	@echo "Coverage report generated in htmlcov/index.html"

test-models:
	python manage.py test main.tests.test_models

test-views:
	python manage.py test main.tests.test_views

lint:
	@echo "Running flake8..."
	flake8 main/ website/
	@echo "Running pylint..."
	pylint --load-plugins=pylint_django --django-settings-module=website.settings main/ website/
	@echo "Running black check..."
	black --check main/ website/
	@echo "Running isort check..."
	isort --check-only main/ website/

format:
	@echo "Formatting with black..."
	black main/ website/
	@echo "Sorting imports with isort..."
	isort main/ website/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	@echo "Cleaned Python cache files"

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

superuser:
	python manage.py createsuperuser

collectstatic:
	python manage.py collectstatic --noinput

run:
	python manage.py runserver

shell:
	python manage.py shell

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-django pytest-cov coverage black isort flake8 pylint pylint-django

check:
	python manage.py check

# Docker команды для тестирования
docker-test:
	docker-compose run --rm web python manage.py test

docker-migrate:
	docker-compose exec web python manage.py migrate

docker-shell:
	docker-compose exec web python manage.py shell

docker-bash:
	docker-compose exec web bash

# CI/CD симуляция
ci-test:
	@echo "Running CI/CD pipeline simulation..."
	@echo "1. Linting..."
	@make lint || true
	@echo "\n2. Running tests..."
	@make test-coverage
	@echo "\n3. Building Docker..."
	@make docker-build
	@echo "\nCI/CD simulation completed!"