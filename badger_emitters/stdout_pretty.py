import json

class stdout_pretty(object):
    def __init__(self, config=None, logger=None): #, configurator, config_dir):
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

        try:
            print json.dumps(payload, sort_keys=True, indent=4, separators=(',', ': '))
        except:
            import sys
            ei = sys.exc_info()
            self.log("err", msg="Could not emit stats!", emitter=__name__, exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])))
