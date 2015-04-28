class load(object):
    def __init__(self, config=None, logger=None):
        self.prefix = "load."
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

    def get_stats(self, global_iteration):
        # take into account custom interval, if present in config
        if global_iteration % self.interval:
            return None

        payload = []

        with open("/proc/loadavg") as loadavg_file:
            loadavg_data = loadavg_file.readline().split()

        payload.append({ self.prefix + "one": {'value': float(loadavg_data[0]), 'units': ''}})
        payload.append({ self.prefix + "five": {'value': float(loadavg_data[1]), 'units': ''}})
        payload.append({ self.prefix + "fifteen": {'value': float(loadavg_data[2]), 'units': ''}})
        payload.append({ self.prefix + "runnable_entities": {'value': int(loadavg_data[3].split("/")[0]), 'units': ''}})
        payload.append({ self.prefix + "total_entities": {'value': int(loadavg_data[3].split("/")[1]), 'units': ''}})

        return payload

if __name__ == "__main__":
    l = load({"interval":0})
    print l.get_stats(0)
