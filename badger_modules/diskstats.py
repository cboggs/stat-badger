import copy
import re

class diskstats(object):
    def __init__(self, logger=None):
        self.prefix = 'cpu.'
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

        for stat in self.disk_stats():
            payload.append(stat)

#        payload.append(self.ctxt_switches(proc_stat, interval))

        return payload


    def disk_stats(self, proc_stat):
        disk_stat = {}

        with open("/proc/diskstats") as fd:
            for line in fd.readlines():
                # Just grab nbd, sda, and hda devices for now
                if len(line) and re.match('^[0-9 ]+(nbd[0-9a-z]+|(h|s)da) ', line):
                    split_line = line.rstrip("\n").split()
                    disk_stat[split_line[2]] = split_line[3:]

        disk_vals = {}
        disk_diffs = {}

        # First run of this module will hit this block and return all zeroes, after populating
        #  self.last_disk_vals. This approach avoids inflated values for should-be-zero states
        #  at first collection
        if not self.last_disk_vals:
            for i, state in enumerate(self.stats):
                if i != 9:
                    self.last_disk_vals[state] = int(jiffie_info[i])

            return [{self.prefix + key: {'value': 0.0, 'units': 'percent'}} for key in self.last_util_vals]

        # We only make it this far if self.last_util_vals has been populated
        total_jiffies = sum(int(j) for j in jiffie_info)
        for i, state in enumerate(self.states):
            if num_states >= i:
                vals[state] = int(jiffie_info[i])

        diff_total_jiffies = total_jiffies - self.last_total_jiffies

        for state in vals.keys():
            diffs[state] = vals[state] - self.last_util_vals[state]

        for state in diffs.keys():
            util[state] =  { 'value': (float(diffs[state]) / float(diff_total_jiffies) * 100), 'units': 'percent' }

        # Get ready for the next run
        self.last_total_jiffies = sum(int(j) for j in jiffie_info)
        self.last_util_vals = copy.deepcopy(vals)

        return [{self.prefix + key: value} for key,value in util.iteritems()]


    def ctxt_switches(self, proc_stat, interval=1):
        #Assume first run, return zero but populate last value
        if not self.last_ctxt_switches:
            self.last_ctxt_switches = int(proc_stat['ctxt'][0])
            return {self.prefix + 'ctxt_per_sec': {'value': 0, 'units': ''}}

        ctxt_switches = int(proc_stat['ctxt'][0])
        ctxt_switches_per_second = (float(ctxt_switches) - float(self.last_ctxt_switches)) / float(interval)
        self.last_ctxt_switches = ctxt_switches

        return {self.prefix + 'ctxt_per_sec': {'value': ctxt_switches_per_second, 'units': ''}}


    def procs_forked(self, proc_stat, interval=1):
        #Assume first run, return zero but populate last value
        if not self.last_procs_forked:
            self.last_procs_forked = int(proc_stat['processes'][0])
            return {self.prefix + 'procs_forked_per_sec': {'value': 0, 'units': ''}}

        procs_forked = int(proc_stat['processes'][0])
        procs_forked_per_second = (float(procs_forked) - float(self.last_procs_forked)) / float(interval)
        self.last_procs_forked = procs_forked

        return {self.prefix + 'procs_forked_per_sec': {'value': procs_forked_per_second, 'units': ''}}



if __name__ == "__main__":
    c = cpu()
    print c.get_metrics()
