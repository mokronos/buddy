class Tool:
    def __init__(self, *, name: str, description: str) -> None:
        self.name = name
        self.description = description

    def run(self, *args, **kwargs):
        raise NotImplementedError
