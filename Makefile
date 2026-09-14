.PHONY: install fixture test demo doctor serve

install:
	pip install -e ".[dev]"

fixture:
	python scripts/make_fixture.py

test:
	pytest

demo:
	alphaclip demo

doctor:
	alphaclip doctor

serve:
	alphaclip serve --host 127.0.0.1 --port 8080
