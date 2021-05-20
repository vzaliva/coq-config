clean:
	rm -rf dist build *.egg-info

build:
	@-$(MAKE) clean
	python setup.py sdist bdist_wheel

publish-prod:
	twine upload --repository pypi dist/*

publish-test:
	twine upload --repository testpypi dist/*