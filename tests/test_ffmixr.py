import unittest
import unittest.mock
import mock
import os
from unittest import TestCase
from unittest.mock import MagicMock, Mock
from ffmixr.rescore import Rescore
import pathlib
from contextlib import contextmanager
from tempfile import TemporaryDirectory
import json

# Found on SO
@contextmanager
def temporary_test_dir():
    oldpwd = os.getcwd()
    with TemporaryDirectory("test-path") as td:
        try:
            os.chdir(td)
            yield
        finally:
            os.chdir(oldpwd)
# from ffmixr import rescore
# from context import ffmixr

configObj = {
    'movie': {
        'name': 'zombieland.mkv',
        'start': '00:04:54.0',
        'end': '00:06:12.0'
    },
    'track': {
        'name': 'I Like It.flac',
        'start': '00:00:04.5',
        'end': '00:01:22.0'
    }}
jsonconfig = json.dumps(configObj)

class TestRescoreValidate(TestCase):
    config = json.loads(jsonconfig)

    @temporary_test_dir()
    def test_validate_pass(self):
        rescore = Rescore(self.config)
        with open(self.config["movie"]["name"], 'w') as moviefile:
            pass
        with open(self.config["track"]["name"], 'w') as musicFile:
            pass
        rescore.validate()
        
    @temporary_test_dir()
    def test_validate_missingmovie(self):
        rescore = Rescore(self.config)
        with open(self.config["track"]["name"], 'w') as musicFile:
            pass
        with self.assertRaises(FileNotFoundError):
            rescore.validate()
        
    @temporary_test_dir()
    def test_validate_missingtrack(self):
        rescore = Rescore(self.config)
        with open(self.config["movie"]["name"], 'w') as moviefile:
            pass
        with self.assertRaises(FileNotFoundError):
            rescore.validate()
            
    @temporary_test_dir()
    def test_validate_bad_time(self):
        rescore = Rescore(self.config)
        with open(self.config["movie"]["name"], 'w') as moviefile:
            pass
        with open(self.config["track"]["name"], 'w') as musicFile:
            pass
        
class TestRescoreCut(TestCase):
    config = json.loads(jsonconfig)
    
    @temporary_test_dir()
    def test_cut(self):
        self.config["movie"]["name"] = "C:\\Users\\thershey\\Documents\\zombielandRemix\\zombieland.mkv"
        rescore = Rescore(self.config)
        rescore.cut_movie()
        
if __name__ == '__main__':
    unittest.main()