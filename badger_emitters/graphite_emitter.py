import pickle
import socket
import struct

class graphite_emitter(object):
    def __init__(self, config=None, logger=None):
        self.log = logger
        self.config = config
        self.carbon_host = self.config['host']
        self.carbon_port = self.config['port']

        if self.log == None:
            import logging
            self.log = logging.getLogger(__name__)
            self.log.setLevel(logging.DEBUG)
            self.log.addHandler(logging.StreamHandler())

#        except:
#            import sys
#            ei = sys.exc_info()
#            self.log("err", msg="Could not connect to InfluxDB!", emitter=__name__, exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])))
#            raise RuntimeError("Failed to connect to InfluxDB")

    def emit_metrics(self, payload):
        stat_tuples = []
        timestamp = int(payload['timestamp'])
        datacenter = payload['datacenter']
        region = payload['region']
        zone = payload['zone']
        cluster = payload['cluster']
        hostname = payload['hostname']
        ipv4 = payload['ipv4']
        ipv6 = payload['ipv6']

        path = ""
        if datacenter:
            path += datacenter + "."
        if region:
            path += region + "."
        if zone:
            path += zone + "."
        if cluster:
            path += cluster + "."

        path += hostname + "."

        for series_data in payload['points']:
            series_name = series_data.keys()[0]
            stat_tuples.append( (path + series_name, (timestamp, series_data[series_name]['value'])) )

        try:
            payload = pickle.dumps(stat_tuples, protocol=2)
        except:
            import sys, traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            return

        try:
            header = struct.pack("!L", len(payload))
        except:
            import sys, traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            return
        else:
            message = header + payload

        try:
            sock = socket.socket()
            sock.connect((self.carbon_host, self.carbon_port))
            sock.sendall(message)
            sock.close()
        except:
            import sys, traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            return
        else:
            self.log("debug", msg="Successfully sent Graphite batch!")
