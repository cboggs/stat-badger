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
            graphite_payload = pickle.dumps(stat_tuples, protocol=2)
        except:
            import sys
            ei = sys.exc_info()
            self.log("err", msg="Failed to pickle Graphite stats", exceptionType="{0}".format(str(ei[0]).split("'")[1]), exception="{0}".format(ei[1]), error="EmitFailed")
            return

        try:
            header = struct.pack("!L", len(graphite_payload))
        except:
            import sys
            ei = sys.exc_info()
            self.log("err", msg="Failed to pack Graphite message", exceptionType="{0}".format(str(ei[0]).split("'")[1]), exception="{0}".format(ei[1]), error="EmitFailed")
            return
        else:
            message = header + graphite_payload

        try:
            sock = socket.socket()
            sock.connect((self.carbon_host, self.carbon_port))
            sock.sendall(message)
            sock.close()
        except:
            import sys
            ei = sys.exc_info()
            self.log("err", msg="Failed to send batch to Graphite", exceptionType="{0}".format(str(ei[0]).split("'")[1]), exception="{0}".format(ei[1]), error="EmitFailed")
            return
        else:
            self.log("debug", msg="Successfully sent batch to Graphite")
