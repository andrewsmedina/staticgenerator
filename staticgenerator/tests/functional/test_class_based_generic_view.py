#from staticgenerator.staticgenerator import StaticGenerator
#from tests.functional import FUNCTIONAL_TESTS_DIR

import unittest
#:import sys
#import os


class ClassBasedGenericViewTestCase(unittest.TestCase):
    pass
    # @classmethod
    # def setUpClass(cls):
    #     sys.path.insert(0, FUNCTIONAL_TESTS_DIR)
    #     os.environ['DJANGO_SETTINGS_MODULE'] = 'mock_settings'

    # @classmethod
    # def tearDownClass(cls):
    #     sys.path.remove(FUNCTIONAL_TESTS_DIR)
    #     del os.environ['DJANGO_SETTINGS_MODULE']

    # def test_publish_from_path(self):
    #     instance = StaticGenerator()
    #     instance.publish_from_path("some_path", content="some_content")
