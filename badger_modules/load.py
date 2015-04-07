class load(object):
    def __init__(self, logger): #, configurator, config_dir):
        self.prefix = "load"
        self.log = logger
        #self.configurator = configurator
        #self.config_dir = config_dir

    def get_metrics(self):
        payload = []

        with open("/proc/loadavg") as loadavg_file:
            loadavg_data = loadavg_file.readline().split()

        payload.append({ self.prefix + ".one": loadavg_data[0]})
        payload.append({ self.prefix + ".five": loadavg_data[1]})
        payload.append({ self.prefix + ".fifteen": loadavg_data[2]})
        payload.append({ self.prefix + ".runnable_entities": loadavg_data[3].split("/")[0]})
        payload.append({ self.prefix + ".total_entities": loadavg_data[3].split("/")[1]})

        return payload
