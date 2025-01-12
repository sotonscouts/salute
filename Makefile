.PHONY: all clean fix lint type test test-cov

CMD:=poetry run
PYMODULE:=salute
MANAGEPY:=$(CMD) ./manage.py
SETTINGS_MODULE:=salute.settings

all: type test format lint
fix: lint-fix format

lint: 
	$(CMD) ruff check $(PYMODULE)

lint-fix: 
	$(CMD) ruff check --fix $(PYMODULE)

check:
	$(MANAGEPY) check

dev:
	$(MANAGEPY) runserver

format:
	$(CMD) ruff format $(PYMODULE)

format-check:
	$(CMD) ruff format --check $(PYMODULE)

type: 
	$(CMD) mypy $(PYMODULE)

test: | $(PYMODULE)
	DJANGO_SETTINGS_MODULE=$(SETTINGS_MODULE) $(CMD) pytest -vv --cov=$(PYMODULE) $(PYMODULE)

test-cov:
	DJANGO_SETTINGS_MODULE=$(SETTINGS_MODULE) $(CMD) pytest -vv --cov=$(PYMODULE) $(PYMODULE) --cov-report html

clean:
	git clean -Xdf # Delete all files in .gitignore