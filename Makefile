.PHONY: all checkmake clean lint run shellcheck style test unittest

all: checkmake shellcheck style lint test

checkmake:
	checkmake ./Makefile

clean:

lint:
	pylint --rcfile=./.pylintrc *.py || true
	pylint --rcfile=./.pylintrc ./tests/*.py || true

run:
	python ./main.py

shellcheck:
	shellcheck 0 || true
	shellcheck 4 || true

style:
	pycodestyle *.py || true


unittest:
	python -m unittest tests/test_escape_text.py

test: unittest
