import unittest
from koursaros.modeling import model_from_yaml
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

class TrainTest(unittest.TestCase):

    def test_train_classifier(self):
        model = model_from_yaml(os.path.join(dir_path, 'samples/classifier.yaml'))
        model.train(force_build_features=True)
        assert(os.path.exists(model.ckpt_dir))

    def test_train_regression(self):
        model = model_from_yaml(os.path.join(dir_path, 'samples/regression.yaml'))
        model.train(force_build_features=True)
        assert (os.path.exists(model.ckpt_dir))

    def test_run_classifier(self):
        model = model_from_yaml(os.path.join(dir_path, 'samples/classifier.yaml'))
        res = model.run(['test'], ['test'])
        assert(len(res) == 1)
        assert(type(res[0]) == str)

    def test_run_regression(self):
        model = model_from_yaml(os.path.join(dir_path, 'samples/regression.yaml'))
        res = model.run(['test'], ['test'])
        assert (len(res) == 1)
        assert (type(res[0]) == float)

if __name__ == '__main__':
    unittest.main()