import json
from influxdb import client as influxdb

class influxdb_emitter(object):
    def __init__(self, config=None, logger=None):
        self.log = logger
        self.config = config
        self.columns = ['value', 'units', 'time', 'datacenter', 'region', 'zone', 'cluster', 'hostname', 'ipv4', 'ipv6']
        self.host = self.config['host']
        self.port = self.config['port']
        self.database = self.config['database']
        self.user = self.config['user']
        self.password = self.config['pass']

        if self.log == None:
            import logging
            self.log = logging.getLogger(__name__)
            self.log.setLevel(logging.DEBUG)
            self.log.addHandler(logging.StreamHandler())

        try:
            self.db = influxdb.InfluxDBClient(self.host, self.port, self.user, self.password, self.database)
        except:
            import sys
            ei = sys.exc_info()
            self.log("err", msg="Could not connect to InfluxDB!", emitter=__name__, exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])))
            raise RuntimeError("Failed to connect to InfluxDB")

    def emit_metrics(self, payload):
        influxdb_payload = []
        timestamp = int(payload['timestamp'])
        datacenter = payload['datacenter']
        region = payload['region']
        zone = payload['zone']
        cluster = payload['cluster']
        hostname = payload['hostname']
        ipv4 = payload['ipv4']
        ipv6 = payload['ipv6']

        for series_data in payload['points']:
            series_name = series_data.keys()[0]
            influxdb_payload.append({
                'name': series_name,
                'columns': self.columns,
                'points': [[series_data[series_name]['value'], series_data[series_name]['units'], timestamp, datacenter, region, zone, cluster, hostname, ipv4, ipv6]]
            })

        try:
            self.db.write_points(json.dumps(influxdb_payload), time_precision='s')
            #print json.dumps(influxdb_payload)
        except:
            import sys
            ei = sys.exc_info()
            self.log("err", msg="Could not write points to InfluxDB!", emitter=__name__, exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])))
            print json.dumps(influxdb_payload)
            return
