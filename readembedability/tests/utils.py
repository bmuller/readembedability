class FakeResponse:
    def __init__(self, body, url=None):
        self.body = body
        self.url = url

    def isText(self):
        return False
