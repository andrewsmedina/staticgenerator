from setuptools import setup

version = '1.5.1'

tests_require = [
    'coverage',
    'mox',
    'django-nose',
    'nose',
    'django==1.4.22',
]

setup(
    name='staticgenerator',
    version=version,
    description="StaticGenerator for Django",
    author="Jared Kuolt",
    author_email="me@superjared.com",
    url="http://superjared.com/projects/static-generator/",
    packages=['staticgenerator'],
    extras_require={
        'tests': tests_require,
    },
)
