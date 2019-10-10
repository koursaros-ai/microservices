import unittest

class DeployTest(unittest.TestCase):

    def setUp(self):
        pass # functions that will be executed before every test

    def tearDown(self):
        pass # functions that will be executed after every test

    def test_something(self):
        self.assertEqual('foo'.upper(), 'FOO')

if __name__ == '__main__':
    unittest.main()