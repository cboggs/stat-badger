import json
import urllib2

class influxdb08_emitter(object):
    def __init__(self, config=None, logger=None):
        self.log = logger
        self.config = config

        if not self.config['interval']:
            self.interval = 1
        else:
            self.interval = self.config['interval']

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

        self.url = "http://{0}:{1}/db/{2}/series?u={3}&p={4}&time_precision=s".format(self.host, self.port, self.database, self.user, self.password)
        self.log("debug", msg=self.url)

    def emit_stats(self, payload, global_iteration):
        # take into account custom interval, if present in config
        if global_iteration % self.interval:
            return

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

        req = urllib2.Request(self.url, json.dumps(influxdb_payload), {'Content-Type': 'application/json'})

        try:
            urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            self.log("err", msg="InfluxDB ingest request failed. Response: {0}".format(e), error="EmitFailed")
        else:
            self.log("debug", msg="Successfully sent batch to InfluxDB")
