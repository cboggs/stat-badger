import copy

class cpu(object):
    def __init__(self, logger=None): #, configurator, config_dir):
        self.prefix = 'cpu.'
        self.log = logger
        #self.configurator = configurator
        #self.config_dir = config_dir

        # These store the recent run's values to let us diff and derive % utilization
        self.last_vals = {}
        self.last_total_jiffies = 0
        self.states = ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest_nice']

        if self.log == None:
            import logging
            self.log = logging.getLogger(__name__)
            self.log.setLevel(logging.DEBUG)
            self.log.addHandler(logging.StreamHandler())

    def get_metrics(self):
        payload = []

        return self.cpu_util_percent()

    def cpu_util_percent(self):
        with open("/proc/stat") as statinfo:
            jiffie_line = statinfo.readline().split()

        vals = {}
        diffs = {}
        util = {}
        total_jiffies = 0
        diff_total_jiffies = 0
        num_states = len(jiffie_line) - 1

        # First run of this module will hit this block and return all zeroes, after populating
        #  self.last_vals. This approach avoids inflated values for should-be-zero states
        #  at first collection
        if not self.last_vals:
            self.last_total_jiffies = sum(int(j) for j in jiffie_line[1:])
            for i, state in enumerate(self.states):
                if num_states >= i:
                    self.last_vals[state] = int(jiffie_line[i+1])

            return [{self.prefix + key: {'value': 0.0, 'units': 'percent'}} for key in self.last_vals]

        # We only make it this far if self.last_vals has been populated
        total_jiffies = sum(int(j) for j in jiffie_line[1:])
        for i, state in enumerate(self.states):
            if num_states >= i:
                vals[state] = int(jiffie_line[i+1])

        diff_total_jiffies = total_jiffies - self.last_total_jiffies

        for state in vals.keys():
            diffs[state] = vals[state] - self.last_vals[state]

        for state in diffs.keys():
            util[state] =  { 'value': (float(diffs[state]) / float(diff_total_jiffies) * 100), 'units': 'percent' }

        # Get ready for the next run
        self.last_total_jiffies = sum(int(j) for j in jiffie_line[1:])
        self.last_vals = copy.deepcopy(vals)

        return [{self.prefix + key: value} for key,value in util.iteritems()]


if __name__ == "__main__":
    c = cpu()
    print c.get_metrics()
