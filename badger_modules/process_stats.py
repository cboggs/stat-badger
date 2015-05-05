import copy
import os
import re

###
# Please note that this module is kind of experimental.
# You should ensure that the patterns specified in your config are as specific
#  as you can make them. Making them too greedy will probably not give you the
#  results you expect, as the module will find the first match in /proc and 
#  return results for it - which may or may not be the actual process you're
#  trying to monitor.

class process_stats(object):
    def __init__(self, config=None, logger=None):
        self.prefix = 'proc.'
        self.log = logger
        self.config = config
        
        if not self.config['interval']:
            self.interval = 1
        else:
            self.interval = self.config['interval']

        # These store the recent run's values to let us diff and derive % utilization
        self.last_cpu_vals = {}
        self.last_ctxt_vals = {}
        self.last_total_jiffies = 0
        self.pid_map = {}
        self.found_pids = {}
        self.proc_patterns = self.config['processes']

        if not self.proc_patterns:
            raise Exception("No patterns present in proc_stats module config. Bailing out on module initialization.")

        # strip whitespace out of patterns so they can be matched against /proc data
        for proc in self.proc_patterns:
            proc["pattern"] = proc["pattern"].replace(" ","")
            self.found_pids[proc['name']] = 0

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

        # It's unnecessary to map pids every iteration. Shoot for every 5 seconds instead
        if not global_iteration % 5:
            self.find_pids()

        for stat in self.proc_cpu():
            payload.append(stat)

        for stat in self.proc_ctxt():
            payload.append(stat)

        for stat in self.proc_mem():
            payload.append(stat)

        return payload


    def find_pids(self):
        pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        self.pid_map = {}

        for proc in self.found_pids:
            self.found_pids[proc] = 0
    
        for pid in pids:
            self.pid_map[pid] =  open(os.path.join('/proc', pid, 'cmdline'), 'rb').read().replace(b'\0','')

        for proc in self.proc_patterns:
            for pid in self.pid_map:
                try:
                    if re.match(proc['pattern'], self.pid_map[pid]):
                        self.found_pids[proc['name']] = pid
                except IOError: # proc has already terminated
                    continue

    def get_ctxt_info_for_pid(self, pid):
        try:
            ctxt_info = [l.rstrip().split() for l in open("/proc/{0}/status".format(pid)).readlines()[39:41]]
        except IOError: #proc has already terminated
            return None

        return [ctxt_info[0][1], ctxt_info[1][1]]
        

    def get_total_system_jiffies(self):
        return sum(int(j) for j in open("/proc/stat").readlines()[0].split()[1:])

    def get_total_jiffies_for_pid(self, pid):
        try:
            jiffies = sum(int(j) for j in open("/proc/{0}/stat".format(pid)).read().split()[13:17])
        except IOError: # proc has already terminated
            return None

        return jiffies

    def proc_mem(self):
        vals = {}

        for proc, pid in self.found_pids.iteritems():
            try:
                vals[proc] = int(open("/proc/{0}/status".format(pid)).readlines()[16].split()[1]) * 1024
            except IOError: # proc has already terminated
                vals[proc] = 0
    
        return [{self.prefix + "mem_resident." + key: {'value': value, 'units': 'B'}} for key, value in vals.iteritems()]
    
    
    def proc_ctxt(self):
        if not self.last_ctxt_vals:
            for proc, pid in self.found_pids.iteritems():
                ctxt_info = self.get_ctxt_info_for_pid(pid)

                if ctxt_info:
                    self.last_ctxt_vals['voluntary_ctxt_per_sec.' + proc] = int(ctxt_info[0])
                    self.last_ctxt_vals['nonvoluntary_ctxt_per_sec.' + proc] = int(ctxt_info[1])
                else:
                    self.last_ctxt_vals['voluntary_ctxt_per_sec.' + proc] = 0 
                    self.last_ctxt_vals['nonvoluntary_ctxt_per_sec.' + proc] = 0

            return [{self.prefix + key: {'value': 0, 'units': ''}} for key, value in self.last_ctxt_vals.iteritems()]
            
        vals = {}
        diffs = {}
        rates = {}

        for proc, pid in self.found_pids.iteritems():
            ctxt_info = self.get_ctxt_info_for_pid(pid)

            if ctxt_info:
                vals['voluntary_ctxt_per_sec.' + proc] = int(ctxt_info[0])
                vals['nonvoluntary_ctxt_per_sec.' + proc] = int(ctxt_info[1])

                diffs['voluntary_ctxt_per_sec.' + proc] = vals['voluntary_ctxt_per_sec.' + proc] - self.last_ctxt_vals['voluntary_ctxt_per_sec.' + proc]
                diffs['nonvoluntary_ctxt_per_sec.' + proc] = vals['nonvoluntary_ctxt_per_sec.' + proc] - self.last_ctxt_vals['nonvoluntary_ctxt_per_sec.' + proc]

                rates['voluntary_ctxt_per_sec.' + proc] = diffs['voluntary_ctxt_per_sec.' + proc] / self.interval
                rates['nonvoluntary_ctxt_per_sec.' + proc] = diffs['nonvoluntary_ctxt_per_sec.' + proc] / self.interval
            else:
                # Have to re-populate vals dict lest we copy an empty dict into
                # self.last_ctxt_vals which causes KeyErrors when encoutering transient
                # or restarted procs
                vals['voluntary_ctxt_per_sec.' + proc] = 0
                vals['nonvoluntary_ctxt_per_sec.' + proc] = 0
                rates['voluntary_ctxt_per_sec.' + proc] = 0
                rates['nonvoluntary_ctxt_per_sec.' + proc] = 0

        self.last_ctxt_vals = copy.deepcopy(vals)

        return [{self.prefix + key: {'value': value, 'units': ''}} for key, value in rates.iteritems()]


    def proc_cpu(self):
#        # First run of this module will hit this block and return all zeroes, after populating
#        #  self.last_cpu_vals. This approach avoids inflated values for should-be-zero states
#        #  at first collection
        if not self.last_cpu_vals:
            self.last_total_jiffies = self.get_total_system_jiffies()
            for proc, pid in self.found_pids.iteritems():
                self.last_cpu_vals[proc] = self.get_total_jiffies_for_pid(pid)

            return [{self.prefix + "cpu." + key: {'value': 0.0, 'units': 'percent'}} for key in self.last_cpu_vals]

        # We only make it this far if self.last_cpu_vals has been populated
        vals = {}
        diffs = {}
        util = {}

        current_total_jiffies = self.get_total_system_jiffies()
        new_jiffies = current_total_jiffies - self.last_total_jiffies

        for proc, pid in self.found_pids.iteritems():
            vals[proc] = self.get_total_jiffies_for_pid(pid)
            if self.last_cpu_vals[proc] and vals[proc]:
                # proc appears to still be present, find utilization
                diffs[proc] = vals[proc] - self.last_cpu_vals[proc]
                util[proc] =  { 'value': (float(diffs[proc]) / float(new_jiffies)) * 100, 'units': 'percent' }
            else:
                # proc is not running under this pid anymore, report zero
                # this does mean that if the proc respawned under a new pid,
                # utilization will be missed until the next pid mapping takes place
                self.last_cpu_vals[proc] = 0
                util[proc] =  { 'value': 0.0, 'units': 'percent'}

#        # Get ready for the next run
        self.last_cpu_vals = copy.deepcopy(vals)
        self.last_total_jiffies = current_total_jiffies

        return [{self.prefix + "cpu." + key: value} for key,value in util.iteritems()]


if __name__ == "__main__":
    import time
    cfg = { 
        "interval": 0,
        "blacklist": [],
        "processes": [
#            { "name": "stat-badger", "pattern": ".+badger_core\.py -f.+" }
        ]
    }
    p = process_stats(config=cfg)
    i = 0
    while True:
        print p.get_stats(i)
        i += 1
        time.sleep(1)
