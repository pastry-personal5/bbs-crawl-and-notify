lint:
	pylint ./*.py
	pylint ./tests/test_escape_text.py

run:
	python ./main.py

unittest:
	python -m unittest tests/test_escape_text.py

test: unittest
