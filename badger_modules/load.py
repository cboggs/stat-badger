class load(object):
    def __init__(self, logger): #, configurator, config_dir):
        self.log = logger
        #self.configurator = configurator
        #self.config_dir = config_dir

    def get_metrics(self):
        self.log("debug", metrics=[{"load.one":3.2}, {"load.five":1.4}, {"load.fifteen":0.9}], module=__name__)
