release: test
	rm -rf dist
	python setup.py sdist bdist_wheel upload
test:
	pep8 readembedability
	pylint readembedability
	python -m unittest
