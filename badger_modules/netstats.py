import copy
import re

class netstats(object):
    def __init__(self, config=None, logger=None):
        self.prefix = 'net.'
        self.log = logger
        self.config = config

        if self.config:
            self.interfaces_to_check = self.config['interfaces_to_check']
        else:
            self.interfaces_to_check = []

        # These store the recent run's values to let us diff and derive % utilization
        self.last_net_vals = {}
        self.stats = ['rx_bytes', 'rx_packets', 'rx_errs', 'rx_drop', 'rx_fifo', 'rx_frame', 'rx_compressed', 'rx_multicast', 'tx_bytes', 'tx_packets', 'tx_errs', 'tx_drop', 'tx_fifo', 'tx_colls', 'tx_carier', 'tx_compressed']

        if self.log == None:
            import logging
            self.log = logging.getLogger(__name__)
            self.log.setLevel(logging.DEBUG)
            self.log.addHandler(logging.StreamHandler())

    def get_metrics(self, interval=1):
        payload = []

        for stat in self.net_stats(interval):
            payload.append(stat)

        return payload


    def net_stats(self, interval):
        net_stat = {}

        with open("/proc/net/dev") as fd:
            # Throw away the first two lines
            fd.readline()
            fd.readline()

            for line in fd.readlines():
                split_line = line.rstrip("\n").split()
                if not self.interfaces_to_check or split_line[0].split(":")[0] in self.interfaces_to_check:
                    net_stat[split_line[0].split(":")[0]] = split_line[1:]

        net_vals = {}
        net_vals_per_sec = {}

        # First run of this module will hit this block and return all zeroes, after populating
        #  self.last_disk_vals. This approach avoids inflated values for should-be-zero states
        #  at first collection
        if not self.last_net_vals:
            for i, stat in enumerate(self.stats):
                for iface in net_stat.keys():
                    self.last_net_vals[stat + "." + iface] = int(net_stat[iface][i])

            return [{self.prefix + key: {'value': 0.0, 'units': ''}} for key in self.last_net_vals]

        # We only make it this far if self.last_disk_vals has been populated
        for i, stat in enumerate(self.stats):
            for iface in net_stat.keys():
                net_vals[stat + "." + iface] = int(net_stat[iface][i])

        for i, stat in enumerate(self.stats):
            for iface in net_stat.keys():
                net_vals_per_sec[stat + "." + iface] = {'value': ((int(net_vals[stat + "." + iface]) - int(self.last_net_vals[stat + "." + iface])) / interval), 'units': ''}
                if stat in ['rx_bytes', 'tx_bytes']:
                    net_vals_per_sec[stat + "." + iface]['units'] = 'B'

                    # No one likes doing this math in their head when looking at graphs
                    net_vals_per_sec[stat.split("_")[0] + "_bits." + iface] = {'value': (int(net_vals_per_sec[stat + "." + iface]['value']) * 8), 'units': 'b'}

        self.last_net_vals = copy.deepcopy(net_vals)

        return [{self.prefix + key: value} for key,value in net_vals_per_sec.iteritems()]


if __name__ == "__main__":
    n = netstats()
    print n.get_metrics()
