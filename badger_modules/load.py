class load(object):
    def __init__(self, logger=None): #, configurator, config_dir):
        self.prefix = "load"
        self.log = logger
        #self.configurator = configurator
        #self.config_dir = config_dir

        if self.log == None:
            import logging
            self.log = logging.getLogger(__name__)
            self.log.setLevel(logging.DEBUG)
            self.log.addHandler(logging.StreamHandler())

    def get_metrics(self):
        payload = []

        with open("/proc/loadavg") as loadavg_file:
            loadavg_data = loadavg_file.readline().split()

        payload.append({ self.prefix + ".one": {'value': loadavg_data[0], 'units': ''}})
        payload.append({ self.prefix + ".five": {'value': loadavg_data[1], 'units': ''}})
        payload.append({ self.prefix + ".fifteen": {'value': loadavg_data[2], 'units': ''}})
        payload.append({ self.prefix + ".runnable_entities": {'value': loadavg_data[3].split("/")[0], 'units': ''}})
        payload.append({ self.prefix + ".total_entities": {'value': loadavg_data[3].split("/")[1], 'units': ''}})

        return payload

if __name__ == "__main__":
    l = load()
    print l.get_metrics()
