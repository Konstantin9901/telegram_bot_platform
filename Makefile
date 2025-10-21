.PHONY: install-dev test lint coverage format run token auth-test

install-dev:
	source venv/bin/activate && pip install -r requirements-dev.txt

test:
	source venv/bin/activate && pytest tests --disable-warnings

lint:
	source venv/bin/activate && ruff check app tests

coverage:
	source venv/bin/activate && pytest --cov=app --cov=tests --cov-report=term-missing

format:
	source venv/bin/activate && ruff format app tests

run:
	source venv/bin/activate && uvicorn app.main:app --reload

token:
	source venv/bin/activate && python scripts/generate_token.py

auth-test:
	source venv/bin/activate && python scripts/auth_test.py

dev:
	uvicorn app.main:app --reload

db-init:
	python -c "from app.database import Base, engine; from app import models; Base.metadata.create_all(bind=engine)"
