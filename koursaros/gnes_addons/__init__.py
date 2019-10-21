from gnes.flow import Flow as _Flow


class Flow(_Flow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_client(self, **kwargs):
        self._client_node = kwargs


