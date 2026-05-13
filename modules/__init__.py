class BaseModule:
    keys = []

    def __init__(self, api, config):
        self.api = api
        self.config = config

    def start(self):
        pass

    def stop(self):
        pass

    def refresh(self):
        pass