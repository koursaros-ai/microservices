
from inspect import getsource


class ClassBottler:
    """Class that formats a python class by being
    given a set of attributes and formatting them
    based on what type of object they are
    """
    @staticmethod
    def check_name(name, obj):
        if name is None:
            raise NameError(f'"None" as name for obj: {obj}')

    class Plain(str):
        """Wrap to indicate that the variable should not
        have quotes around the value
        """

    invalid_names = ['from']
    plain_types = (list, int, Plain, type(None))

    def __init__(self, name, parent_class=None):
        self.lines = []
        self.classes = []
        self.headers = []
        self.name = name
        self.parent = f'({parent_class})' if parent_class else ''

    def digest(self, obj, name=None):
        if name in self.invalid_names:
            raise ValueError(f'Invalid Attribute Name: "{name}"')

        if isinstance(obj, self.plain_types):
            self.check_name(name, obj)
            self.lines.append(f'{name} = {obj}')

        elif isinstance(obj, str):
            self.check_name(name, obj)
            self.lines.append(f'{name} = "{obj}"')

        elif isinstance(obj, dict):
            for key, value in obj.items():
                self.digest(value, name=key)

        # class or function
        elif callable(obj):
            self.lines += getsource(obj).split('\n')

        # append in order to bottle later
        elif isinstance(obj, ClassBottler):
            self.classes.append(obj)

        else:
            raise NotImplementedError(f'var "{name}" of type '
                                      f'{type(obj)} not supported')

    def bottle(self, indents=0):
        """recursive function to indent each subclass nested
        within a ClassCompiler.Class
        """
        indent = '    ' * indents
        cap = self.headers + [f'{indent}class {self.name}{self.parent}:']
        indent = '    ' * (indents + 1)
        lines = [indent + line for line in self.lines]
        self.lines = cap + lines

        indents += 1

        for cls in self.classes:
            cls.bottle(indents=indents)
            self.lines += cls.lines

    def add_headers(self, headers):
        self.headers += headers

    def to_string(self):
        self.bottle()
        return '\n'.join(self.lines)