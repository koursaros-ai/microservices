import unittest
from koursaros.modeling import model_from_yaml
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

class TrainTest(unittest.TestCase):

    def test_train_classifier(self):
        model = model_from_yaml(os.path.join(dir_path, 'samples/classifier.yaml'))
        model.train(force_build_features=True)

    def test_train_regression(self):
        model = model_from_yaml(os.path.join(dir_path, 'samples/regression.yaml'))

    def test_run_classifier(self):
        model = model_from_yaml(os.path.join(dir_path, 'samples/classifier.yaml'))

    def test_run_regression(self):
        model = model_from_yaml(os.path.join(dir_path, 'samples/regression.yaml'))

if __name__ == '__main__':
    unittest.main()