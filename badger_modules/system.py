import re

class system(object):
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

    def get_stats(self, global_iteration):
        if global_iteration % self.interval:
            return None

        payload = []

        for item in self.cpu_info():
            payload.append(item)

        payload.append({'disk.count': self.disk_count()})

        return payload

    def cpu_info(self):
        with open("/proc/cpuinfo") as c:
            cpuinfo = c.read()

        cpuinfo_lines = cpuinfo.split('\n')
        
        cpu_cores = int(cpuinfo.count("processor\t: "))
        cpu_speed = float(cpuinfo_lines[7].split(": ")[1])
        cpu_cache_size = int(cpuinfo_lines[8].split(": ")[1].split()[0])

        return [
            { 'cpu.cores': {'value': cpu_cores, 'units': ''}},
            { 'cpu.speed': {'value': cpu_speed, 'units': 'MHz'}},
            { 'cpu.cache_size': {'value': cpu_cache_size, 'units': 'KB'}}
        ]

    def disk_count(self):
        disk_count = 0

        with open("/proc/partitions") as partinfo:
            for line in partinfo:
                if re.match('.+ (s|xv)d[a-z]+$', line):
                    disk_count += 1

        return {'value': int(disk_count), 'units': ''}
            

if __name__ == "__main__":
    s = system(config={"interval":0})
    print s.get_stats(0)
