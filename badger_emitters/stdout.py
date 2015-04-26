class stdout(object):
    def __init__(self, config=None, logger=None):
        self.log = logger
        self.config = config

        if not self.config['interval']:
            self.interval = 1
        else:
            self.interval = self.config['interval']

        if self.log == None:
            import logging
            self.log = logging.getLogger(__name__)
            self.log.setLevel(logging.DEBUG)
            self.log.addHandler(logging.StreamHandler())

    def emit_stats(self, payload, global_iteration):
        # take into account custom interval, if present in config
        if global_iteration % self.interval:
            return

        print payload
