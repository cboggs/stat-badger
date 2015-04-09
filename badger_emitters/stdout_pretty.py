import json

class stdout_pretty(object):
    def __init__(self,logger): #, configurator, config_dir):
        self.log = logger
        #self.configurator = configurator
        #self.config_dir = config_dir

    def emit_metrics(self, payload):
        try:
            print json.dumps(payload, sort_keys=True, indent=4, separators=(',', ': '))
        except:
            import sys
            ei = sys.exc_info()
            self.log("err", msg="Could not emit metrics!", emitter=__name__, exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])))
