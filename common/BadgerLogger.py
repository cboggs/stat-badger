import logging
import json

class BadgerLogger(object):
    def __init__(self, logLevel="debug", dest=None):

        if logLevel.lower() == "debug":
            self.logLevel = logging.DEBUG
        elif logLevel.lower() == "info":
            self.logLevel = logging.INFO
        elif logLevel.lower() == "warning" or logLevel == "warn":
            self.logLevel = logging.WARNING
        else:
            print "You didn't provide a valid log level! Exiting."
            exit(1)

        print self.logLevel

        logging.basicConfig(level=self.logLevel, format='%(message)s')

    def logJSON(self, logLevel="unknown", **kwargs):
        if logLevel == "unknown":
            kwargs['logFail'] = "No value given for logLevel, assuming 'unknown'"

        logLevel = logLevel.lower()
        kwargs['logLevel'] = logLevel

        try:
            if logLevel == "debug":
                logging.debug(json.dumps(kwargs))
            elif logLevel == "info":
                logging.info(json.dumps(kwargs))
            elif logLevel == "warning" or logLevel == "warn":
                logging.warning(json.dumps(kwargs))
            elif logLevel == "error" or logLevel == "err" or logLevel == "unknown":
                logging.error(json.dumps(kwargs))
            elif logLevel == "critical" or logLevel == "crit":
                kwargs['exited'] = True
                logging.critical(json.dumps(kwargs))
                exit(3)
                
        except:
            import traceback, sys
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            del ei

    def getLogLevel(self):
        print "LogLevel in BadgerLogger: {0}".format(self.logLevel)
