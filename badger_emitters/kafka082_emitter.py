import json
from kafka import SimpleProducer, KafkaClient

class kafka082_emitter(object):
    def __init__(self, config=None, logger=None):
        self.log = logger
        self.config = config

        # Hush up the kafka module's logger
        import logging

        if self.log == None:
            import logging
            self.log = logging.getLogger(__name__)
            self.log.setLevel(logging.DEBUG)
            self.log.addHandler(logging.StreamHandler())

        if not self.config['interval']:
            self.interval = 1
        else:
            self.interval = self.config['interval']

        if (not "codec" in self.config) or (self.config['codec'] == "none"):
            self.codec = 0x00
            self.log("debug", msg="No codec section found in config or codec value is 'none'. Falling back to NO compression for Kafka messages.")
        elif self.config['codec'] == "gzip":
            self.codec = 0x01
            self.log("debug", msg="'gzip' codec selected for Kafka messages.")
        elif self.config['codec'] == "speedy":
            self.codec = 0x02
            self.log("debug", msg="'speedy' codec selected for Kafka messages.")
        else:
            self.log("warn", msg="Unrecognized codec '{0}'. Falling back to NO compression for Kafka messages.".format(self.config['codec']))
            self.codec = 0x00

        self.brokers = self.config['brokers']
        self.topic = self.config['topic']

        # hush up the kafka logger
        logging.getLogger("kafka").setLevel(logging.INFO)

        self.client = KafkaClient(self.brokers)
        self.producer = SimpleProducer(self.client, codec=self.codec)


    def emit_stats(self, payload, global_iteration):
        # take into account custom interval, if present in config
        if global_iteration % self.interval:
            return

        try:
            self.producer.send_messages(self.topic, json.dumps(payload))
        except:
            import sys, traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
        else:
            self.log("debug", msg="Successfully sent batch to Kafka.")
