import os
import re


def find_pipe_path(path):
    current_path = ''
    for directory in path.split('/'):
        current_path += directory + '/'
        test_path = current_path + '.koursaros'
        if os.path.isdir(test_path):
            return current_path

    return None


def parse_stub_string(stub_string):
    s = r'\s*'
    ns = r'([^\s]*)'
    nsp = r'([^\s]+)'
    full_regex = rf'{s}{nsp}\({s}{ns}{s}\){s}->{s}{ns}{s}\|{s}{ns}{s}'
    full_regex = re.compile(full_regex)
    example = '\nExample: <service>( [variable] ) -> <returns> | <destination>'
    groups = full_regex.match(stub_string)

    if not groups:
        raise ValueError(f'\n"{stub_string}" does not match stub string regex{example}')

    groups = groups.groups()
    groups = groups[0].split('.') + list(groups[1:])
    groups = tuple(group if group else None for group in groups)

    return groups
