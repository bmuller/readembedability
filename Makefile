test:
	trial readembedability

lint:
	pep8 --ignore=E303,E251,E201,E202 ./readembedability --max-line-length=140
	find ./readembedability -name '*.py' | xargs pyflakes

install:
	python setup.py install
