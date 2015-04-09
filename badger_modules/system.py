class system(object):
    def __init__(self, logger=None): #, configurator, config_dir):
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

        for item in self.cpu_info():
            payload.append(item)

        payload.append({'mem.total': self.mem_total()})

        return payload

    def cpu_info(self):
        with open("/proc/cpuinfo") as c:
            cpuinfo = c.read()

        cpuinfo_lines = cpuinfo.split('\n')
        
        cpu_cores = cpuinfo.count("processor\t: ")
        cpu_speed = cpuinfo_lines[7].split(": ")[1]
        cpu_cache_size = cpuinfo_lines[8].split(": ")[1]

        return [
            { 'cpu.cores': {'value': cpu_cores, 'units': ''}},
            { 'cpu.speed': {'value': cpu_speed, 'units': 'MHz'}},
            { 'cpu.cache_size': {'value': cpu_cache_size, 'units': 'KB'}}
        ]

    def mem_total(self):
        with open("/proc/meminfo") as meminfo:
            mem_total = meminfo.readline().split()[1]
        return {'value': mem_total, 'units': 'KB'}

if __name__ == "__main__":
    s = system()
    print s.get_metrics()
