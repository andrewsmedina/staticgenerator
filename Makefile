dependencies:
	pip install -e .[tests]

clean:
	@echo "Cleaning up build and *.pyc files..."
	@find . -name '*.pyc' -exec rm -rf {} \;
	@rm -rf build
	@echo "removing (.coverage)"
	@rm -f .coverage
	@echo "removing (test_data)"
	@rm -rf `pwd`/test_data
	@echo "Done!"

test: clean dependencies
	@echo "Running all tests..."
	@mkdir `pwd`/test_data
	@export PYTHONPATH=`pwd`:`pwd`/staticgenerator::$$PYTHONPATH && \
		DJANGO_SETTINGS_MODULE=tests.mock_settings nosetests -d -s --verbose --with-coverage --cover-inclusive --cover-package=staticgenerator \
			staticgenerator/tests
