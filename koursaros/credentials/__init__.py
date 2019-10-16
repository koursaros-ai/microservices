import yaml
from pathlib import Path
from box import Box
import git


DIR = Path(__file__).parent.absolute()


class FileCred(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!file'

    def __init__(self, relative_path):
        path = self.repo_path.joinpath(relative_path)
        self.bytes = path.read_bytes()
        self.text = path.read_text()
        self.path = str(path)

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(node.value)

    @classmethod
    def set_repo_path(cls, repo_path):
        cls.repo_path = repo_path


def get_creds(repo, username='', password=''):
    repo_path = DIR.joinpath(repo)
    repo_path.mkdir(exist_ok=True, parents=True)
    FileCred.set_repo_path(repo_path)
    git.Git(repo_path).clone("https://%s@%sgithub.com/%s" % (username, password, repo))
    creds = yaml.safe_load(repo_path.joinpath('creds.yaml').read_text())
    return Box(creds['creds'])


