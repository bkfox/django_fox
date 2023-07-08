__all__ = ("File",)


class File:
    def __init__(self, data=""):
        self.data = data

    def read(self):
        return self.data

    def write(self, data):
        self.data += data

    def close(self):
        self.data = None

    def __enter__(self):
        return self

    def __exit__(self, *_, **__):
        pass
