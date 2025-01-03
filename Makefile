.PHONY: install migrate run test lint format clean docker-build docker-up docker-down

install:
	pip install -r requirements.txt

migrate:
	python manage.py makemigrations
	python manage.py migrate

run:
	python manage.py runserver

test:
	pytest

lint:
	flake8 .
	black . --check
	isort . --check-only

format:
	black .
	isort .

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +

docker-build:
	docker-compose build

docker-up:
	docker-compose up

docker-down:
	docker-compose down

shell:
	python manage.py shell

collectstatic:
	python manage.py collectstatic --noinput

superuser:
	python manage.py createsuperuser
