BACKEND_DIR=backend

.PHONY: format lint

format:
	cd $(BACKEND_DIR) && poetry run isort .
	cd $(BACKEND_DIR) && poetry run black .

lint:
	cd $(BACKEND_DIR) && poetry run black --check .
	cd $(BACKEND_DIR) && poetry run isort --check-only .
	cd $(BACKEND_DIR) && poetry run pylint apps config core server
