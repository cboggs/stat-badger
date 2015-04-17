import copy
import re
import time
import json

class disk(object):
    def __init__(self, config=None, logger=None):
        self.prefix = 'disk.'
        self.log = logger
        self.config = config
        self.disks_to_check = self.config['disks_to_check']

        # These store the recent run's values to let us diff and derive % utilization
        self.last_disk_vals = {}
        self.stats = ['reads', 'reads_merged', 'read_sectors', 'read_time', 'writes', 'writes_merged', 'write_sectors', 'write_time', 'io', 'io_time', 'io_weighted_time']

        if self.log == None:
            import logging
            self.log = logging.getLogger(__name__)
            self.log.setLevel(logging.DEBUG)
            self.log.addHandler(logging.StreamHandler())

    def get_metrics(self, interval=1):
        payload = []

        for stat in self.disk_stats(interval):
            payload.append(stat)

        return payload


    def disk_stats(self, interval):
        disk_stat = {}

        with open("/proc/diskstats") as fd:
            for line in fd.readlines():
                # Just grab nbd, sda, and hda devices for now
                #if len(line) and re.match('^[0-9 ]+(nbd[0-9a-z]+|(h|s)da) ', line):
                #if len(line) and re.match('^[0-9 ]+sda ', line):
                split_line = line.rstrip("\n").split()
                if not self.disks_to_check or split_line[2] in self.disks_to_check:
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

        # We only make it this far if self.last_disk_vals has been populated
        for i, stat in enumerate(self.stats):
            for disk in disk_stat.keys():
                disk_vals[stat + "." + disk] = int(disk_stat[disk][i])

        for i, stat in enumerate(self.stats):
            for disk in disk_stat.keys():
                if stat == "io":
                    disk_vals_per_sec[stat + "." + disk] = {'value': disk_vals[stat + "." + disk], 'units': ''}
                else:
                    disk_vals_per_sec[stat + "." + disk] = {'value': ((int(disk_vals[stat + "." + disk]) - int(self.last_disk_vals[stat + "." + disk])) / interval), 'units': ''}
                    if stat in ['write_time', 'read_time', 'io_time', 'weighted_io_time']:
                        disk_vals_per_sec[stat + "." + disk]['units'] = 'ms'

                    # just because it's always gratifying to see actual throughput...
                    elif stat in ['read_sectors', 'write_sectors']:
                        disk_vals_per_sec[stat.split("_")[0] + "_thruput." + disk] = {'value': (int(disk_vals_per_sec[stat + "." + disk]['value']) * 512), 'units': 'B'}

        self.last_disk_vals = copy.deepcopy(disk_vals)


        return [{self.prefix + key: value} for key,value in disk_vals_per_sec.iteritems()]


if __name__ == "__main__":
    d = disk()
    print d.get_metrics()
