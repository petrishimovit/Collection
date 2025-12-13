BACKEND_DIR=backend

.PHONY: format lint

format:
	cd $(BACKEND_DIR) && poetry run isort .
	cd $(BACKEND_DIR) && poetry run black .

lint:
	cd $(BACKEND_DIR) && poetry run black --check .
	cd $(BACKEND_DIR) && poetry run isort --check-only .
	cd $(BACKEND_DIR) && poetry run pylint apps config core server

poetry export:

	cd $(BACKEND_DIR) && poetry export -f requirements.txt -o ops/requirements/prod.txt --without-hashes
	cd $(BACKEND_DIR) && poetry export -f requirements.txt -o ops/requirements/ci.txt  --without-hashes --with ci
	cd $(BACKEND_DIR) && poetry export -f requirements.txt -o ops/requirements/dev.txt --without-hashes --with dev