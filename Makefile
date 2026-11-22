.PHONY: check test

check:
	python3 -m json.tool providers.json > /dev/null
	python3 -m py_compile server.py test_server.py

test: check
	python3 -m unittest -v test_server.py
