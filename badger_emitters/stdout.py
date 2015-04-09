class stdout(object):
    def __init__(self,logger): #, configurator, config_dir):
        self.log = logger
        #self.configurator = configurator
        #self.config_dir = config_dir

    def emit_metrics(self, payload):
        print payload
