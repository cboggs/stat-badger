class stdout(object):
    def __init__(self, config=None, logger=None):
        self.log = logger
        self.config = config

        if self.log == None:
            import logging
            self.log = logging.getLogger(__name__)
            self.log.setLevel(logging.DEBUG)
            self.log.addHandler(logging.StreamHandler())

    def emit_metrics(self, payload):
        print payload
