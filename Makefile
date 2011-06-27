dependencies: nose django mox coverage

coverage:
	@python -c 'import coverage' 2>/dev/null || pip install coverage

mox:
	@python -c 'import mox' 2>/dev/null || pip install mox

nose:
	@python -c 'import nose' 2>/dev/null || pip install nose

django:
	@python -c 'import django' 2>/dev/null || pip install django

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
		nosetests -d -s --verbose --with-coverage --cover-inclusive --cover-package=staticgenerator \
			staticgenerator/tests

unit: clean dependencies
	@echo "Running unit tests..."
	@export PYTHONPATH=`pwd`:`pwd`/staticgenerator::$$PYTHONPATH && \
		nosetests -d -s --verbose --with-coverage --cover-inclusive --cover-package=staticgenerator \
			staticgenerator/tests/unit
	
functional: clean dependencies
	@echo "Running unit tests..."
	@mkdir `pwd`/test_data
	@export PYTHONPATH=`pwd`:`pwd`/staticgenerator::$$PYTHONPATH && \
		nosetests -d -s --verbose --with-coverage --cover-inclusive --cover-package=staticgenerator \
			staticgenerator/tests/functional
