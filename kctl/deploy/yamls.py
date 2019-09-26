

def compile_yamls(app_path):
    import os
    for root, dirs, files in os.walk(app_path, topdown=False):
        for file in files:
            if file.endswith('.yaml'):
                print(root + file)
