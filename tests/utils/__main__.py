import subprocess
import os

def testTrainer():
    flags = dict()
    # test 1 sentence classification on sample dataset
    subprocess.call('python -m utils.train ')
    # test 3 sentence classification on sample dataset
    subprocess.call('python -m utils.train ')
    # test 3 sentence regression
    subprocess.call('python -m utils.train ')
    assert(os.path.exists())

def testDataLoading():
    pass
    # test loading data from db
    # test loading data from tsv

if __name__ == '__main__':
    testTrainer()