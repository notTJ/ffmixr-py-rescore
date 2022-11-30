# python -m venv env
# tutorial-env\Scripts\activate
# source env/bin/activate
import unittest
import sys

from setuptools import setup, find_packages, Command

class RunUnittestTests(Command):
    description = "run all tests for rescore + other modules.."
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        tests = unittest.TestLoader().discover('.')
        runner = unittest.TextTestRunner()
        results = runner.run(tests)
        print(results)
        sys.exit(not results.wasSuccessful())
