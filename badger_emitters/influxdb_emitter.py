import json
from influxdb import client as influxdb

class influxdb_emitter(object):
    def __init__(self,logger): #, configurator, config_dir):
        self.log = logger
        #self.configurator = configurator
        #self.config_dir = config_dir
        self.columns = ['value', 'units', 'time']

    def emit_metrics(self, payload):
        influxdb_payload = []
        timestamp = int(payload['timestamp'])

        for series_data in payload['points']:
            series_name = series_data.keys()[0]
            influxdb_payload.append({
                'name': series_name,
                'columns': self.columns,
                'points': [[series_data[series_name]['value'], series_data[series_name]['units'], timestamp]]
            })

        try:
            db = influxdb.InfluxDBClient('10.2.10.20', '8086', 'root', 'root', 'codytest')
        except:
            import sys
            ei = sys.exc_info()
            self.log("err", msg="Could not connect to InfluxDB!", emitter=__name__, exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])))
            return

        try:
            db.write_points(json.dumps(influxdb_payload), time_precision='s')
            print json.dumps(influxdb_payload)
        except:
            import sys
            ei = sys.exc_info()
            self.log("err", msg="Could not write points to InfluxDB!", emitter=__name__, exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])))
            print json.dumps(influxdb_payload)
            return
