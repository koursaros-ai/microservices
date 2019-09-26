
import os

BOLD = '\033[1m{}\033[0m'


def find_app_path(path):

    current_path = ''
    for directory in path.split('/'):
        current_path += directory + '/'
        test_path = current_path + '.koursaros'
        if os.path.isdir(test_path):
            return current_path

    return None
