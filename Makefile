.PHONY: check format

check:
	black --check .
	isort --check-only .
	mypy .

format:
	black .
	isort .
