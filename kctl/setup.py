from pathlib import Path
import os, json, subprocess, sys, pwd

HOME = str(Path.home())
CWD = os.getcwd()

BASH_PATHS = ['/etc/profile', f'{HOME}/.bash_profile', f'{HOME}/.bashrc', f'{HOME}/.profile']
ALIAS = f"alias kctl='{sys.executable} -m kctl'"
PYTHONPATH = f'export PYTHONPATH=$PYTHONPATH:{CWD}/'
KCTL_TAG = '#KOURSAROS'

 
def find_executable(executable, path=None):
    """Find if 'executable' can be run. Looks for it in 'path'
    (string that lists directories separated by 'os.pathsep';
    defaults to os.environ['PATH']). Checks for all executable
    extensions. Returns full path or None if no command is found.
    """
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    extlist = ['']
    if os.name == 'os2':
        (_, ext) = os.path.splitext(executable)
        # executable files on OS/2 can have an arbitrary extension, but
        # .exe is automatically appended if no dot is present in the name
        if not ext:
            executable = executable + ".exe"
    elif sys.platform == 'win32':
        pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
        (_, ext) = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext
    for ext in extlist:
        execname = executable + ext
        if os.path.isfile(execname):
            return execname
        else:
            for p in paths:
                f = os.path.join(p, execname)
                if os.path.isfile(f):
                    return f
    else:
        return None


def append_kctl(bash_path, text):
    with open(bash_path, 'w') as fh:
        text += f'\n{KCTL_TAG}\n{PYTHONPATH}\n{ALIAS}\n'
        fh.write(text)


def cache_bash(bash_path, text):
    with open(f'{bash_path}.cache', 'w') as fh:
        fh.write(text)


def get_tag_line(lines):
    for i, line in enumerate(lines):
        if KCTL_TAG in line:
            return i
    return -1


def add_kctl_to_bash(bash_path):

    if os.path.isfile(bash_path):
        with open(bash_path) as fh:
            text = fh.read()
            cache_bash(bash_path, text)
            lines = text.split('\n')
            i = get_tag_line(lines)
            if i != -1:
                lines = lines[:i - 1] + lines[i + 3:]
                text = '\n'.join(lines)
    else:
        text = ''
        
    append_kctl(bash_path, text)


if __name__ == '__main__':

    if len(sys.argv) > 1:
        BASH_PATHS = sys.argv[1:]

    requires_perms = []

    for bash_path in BASH_PATHS:
        
        try:
            add_kctl_to_bash(bash_path)
            print(f'kctl added to {bash_path}')
        except PermissionError as e:
            requires_perms.append(bash_path)
            
    if requires_perms:
        execute = [find_executable('sudo'), sys.executable, sys.argv[0]] + requires_perms
        subprocess.call(execute)


                
