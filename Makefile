release:
	rm -rf dist
	python setup.py sdist bdist_wheel
	gpg --detach-sign -a dist/*.whl
	gpg --detach-sign -a dist/*.gz
	twine upload dist/*
test:
	pep8 readembedability
	pylint readembedability
	python -m unittest
