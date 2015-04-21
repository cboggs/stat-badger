class memory(object):
    def __init__(self, config=None, logger=None): #, configurator, config_dir):
        self.prefix = "mem."
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
        payload = []

        for item in self.mem_stats():
            payload.append(item)

        return payload

    def mem_stats(self):
        mem_stat = []

        with open("/proc/meminfo") as fd:
            for line in fd:
                split_line = line.replace("(", "_").replace(")", "").split()
                if split_line[0] in ["HugePages_Total:", "HugePages_Free:", "HugePages_Rsvd:", "HugePages_Surp:"]:
                    mem_stat.append({self.prefix + split_line[0].split(":")[0].lower():  {'value': int(split_line[1]), 'units': ''}})
                else:
                    mem_stat.append({self.prefix + split_line[0].split(":")[0].lower():  {'value': int(split_line[1]) * 1024, 'units': 'B'}})
                

        return mem_stat 

if __name__ == "__main__":
    m = memory()
    print m.get_stats()
