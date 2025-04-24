.PHONY: all checkmake clean lint run shellcheck style test unittest

all: checkmake shellcheck style lint test

checkmake:
	checkmake ./Makefile

clean:

lint:
	find ./src -name "*.py" | xargs pylint --rcfile=./.pylintrc || true
	find ./tests -name "*.py" | xargs pylint --rcfile=./.pylintrc || true

run:
	python ./src/bbs_crawl_and_notify/main.py

shellcheck:
	shellcheck 0 || true
	shellcheck 1 || true

style:
	find ./src -name "*.py" | xargs pycodestyle || true
	find ./tests -name "*.py" | xargs pycodestyle || true

unittest:
	python -m unittest tests/test_*.py

test: unittest
