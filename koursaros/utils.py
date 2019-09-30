import os


def find_pipe_path(path):
    current_path = ''
    for directory in path.split('/'):
        current_path += directory + '/'
        test_path = current_path + '.koursaros'
        if os.path.isdir(test_path):
            return current_path

    return None