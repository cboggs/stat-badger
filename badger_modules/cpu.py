import copy

class cpu(object):
    def __init__(self, config=None, logger=None): #, configurator, config_dir):
        self.prefix = 'cpu.'
        self.log = logger
        self.config = config
        
        if not self.config['interval']:
            self.interval = 1
        else:
            self.interval = self.config['interval']

        # These store the recent run's values to let us diff and derive % utilization
        self.last_util_vals = {}
        self.last_ctxt_switches= 0
        self.last_procs_forked= 0
        self.last_total_jiffies = 0
        self.states = ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest_nice']

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
        proc_stat = {}

        # This file is kinda busy, and it seems wasteful to crank through it
        #  line-by-line in each method in order to find the releavant lines
        #  Instead just chop it up into a dict here and pass that around
        with open("/proc/stat") as fd:
            for line in fd.readlines():
                if len(line):
                    split_line = line.rstrip("\n").split()
                proc_stat[split_line[0]] = split_line[1:]


        for stat in self.util_percent(proc_stat):
            payload.append(stat)

        payload.append(self.ctxt_switches(proc_stat))
        payload.append(self.procs_forked(proc_stat))
        payload.append({self.prefix + 'procs_running': {'value': int(proc_stat['procs_running'][0]), 'units': ''}})
        payload.append({self.prefix + 'procs_blocked': {'value': int(proc_stat['procs_blocked'][0]), 'units': ''}})


        return payload

    def util_percent(self, proc_stat):
        jiffie_info = proc_stat['cpu']

        vals = {}
        diffs = {}
        util = {}
        total_jiffies = 0
        diff_total_jiffies = 0
        num_states = len(jiffie_info) - 1

        # First run of this module will hit this block and return all zeroes, after populating
        #  self.last_util_vals. This approach avoids inflated values for should-be-zero states
        #  at first collection
        if not self.last_util_vals:
            self.last_total_jiffies = sum(int(j) for j in jiffie_info)
            for i, state in enumerate(self.states):
                if num_states >= i:
                    self.last_util_vals[state] = int(jiffie_info[i])

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


    def ctxt_switches(self, proc_stat):
        #Assume first run, return zero but populate last value
        if not self.last_ctxt_switches:
            self.last_ctxt_switches = int(proc_stat['ctxt'][0])
            return {self.prefix + 'ctxt_per_sec': {'value': 0, 'units': ''}}

        ctxt_switches = int(proc_stat['ctxt'][0])
        ctxt_switches_per_second = (float(ctxt_switches) - float(self.last_ctxt_switches)) / float(self.interval)
        self.last_ctxt_switches = ctxt_switches

        return {self.prefix + 'ctxt_per_sec': {'value': ctxt_switches_per_second, 'units': ''}}


    def procs_forked(self, proc_stat):
        #Assume first run, return zero but populate last value
        if not self.last_procs_forked:
            self.last_procs_forked = int(proc_stat['processes'][0])
            return {self.prefix + 'procs_forked_per_sec': {'value': 0, 'units': ''}}

        procs_forked = int(proc_stat['processes'][0])
        procs_forked_per_second = (float(procs_forked) - float(self.last_procs_forked)) / float(self.interval)
        self.last_procs_forked = procs_forked

        return {self.prefix + 'procs_forked_per_sec': {'value': procs_forked_per_second, 'units': ''}}



if __name__ == "__main__":
    c = cpu()
    print c.get_stats()
