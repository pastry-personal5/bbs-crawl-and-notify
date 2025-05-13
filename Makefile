# Makefile for bbs_crawl_and_notify
# This Makefile is used to run various tasks for the bbs_crawl_and_notify project.
.PHONY: all checkmake clean lint run shellcheck style test unittest

# Variables
PYCODESTYLE_MAX_LINE_LENGTH=512
PYCODESTYLE_OPTIONS=--max-line-length=$(PYCODESTYLE_MAX_LINE_LENGTH)

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
	find ./src -name "*.py" | xargs pycodestyle ${PYCODESTYLE_OPTIONS} || true
	find ./tests -name "*.py" | xargs pycodestyle ${PYCODESTYLE_OPTIONS} || true

unittest:
	python -m unittest tests/test_*.py

test: unittest
