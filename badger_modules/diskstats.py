import copy
import re
import time
import json

class diskstats(object):
    def __init__(self, config=None, logger=None):
        self.prefix = 'disk.'
        self.log = logger

        # These store the recent run's values to let us diff and derive % utilization
        self.last_disk_vals = {}
        self.stats = ['reads', 'read_merges', 'read_sectors', 'read_time', 'writes', 'write_merges', 'write_sectors', 'write_time', 'io', 'io_time', 'io_weighted_time']

        if self.log == None:
            import logging
            self.log = logging.getLogger(__name__)
            self.log.setLevel(logging.DEBUG)
            self.log.addHandler(logging.StreamHandler())

    def get_metrics(self, interval=1):
        payload = []

        for stat in self.disk_stats(interval):
            payload.append(stat)

#        payload.append(self.ctxt_switches(proc_stat, interval))

        return payload


    def disk_stats(self, interval):
        disk_stat = {}

        with open("/proc/diskstats") as fd:
            for line in fd.readlines():
                # Just grab nbd, sda, and hda devices for now
                if len(line) and re.match('^[0-9 ]+(nbd[0-9a-z]+|(h|s)da) ', line):
                    split_line = line.rstrip("\n").split()
                    disk_stat[split_line[2]] = split_line[3:]

        disk_vals = {}
        disk_vals_per_sec = {}

        # First run of this module will hit this block and return all zeroes, after populating
        #  self.last_disk_vals. This approach avoids inflated values for should-be-zero states
        #  at first collection
        if not self.last_disk_vals:
            for i, stat in enumerate(self.stats):
                if stat != "io":
                    for disk in disk_stat.keys():
                        self.last_disk_vals[stat + "." + disk] = int(disk_stat[disk][i])

            return [{self.prefix + key: {'value': 0.0, 'units': ''}} for key in self.last_disk_vals]

        # We only make it this far if self.last_util_vals has been populated
        for i, stat in enumerate(self.stats):
            if stat != "io":
                for disk in disk_stat.keys():
                    disk_vals[stat + "." + disk] = int(disk_stat[disk][i])

        for i, stat in enumerate(self.stats):
            if stat != "io":
                for disk in disk_stat.keys():
                    disk_vals_per_sec[stat + "." + disk] = {'value': ((int(disk_vals[stat + "." + disk]) - int(self.last_disk_vals[stat + "." + disk])) / interval), 'units': ''}
                    if stat in ['write_time', 'read_time', 'io_time', 'weighted_io_time']:
                        disk_vals_per_sec[stat + "." + disk]['units'] = 'ms'

        self.last_disk_vals = copy.deepcopy(disk_vals)


        return [{self.prefix + key: value} for key,value in disk_vals_per_sec.iteritems()]


if __name__ == "__main__":
    d = diskstats()
    print d.get_metrics()
