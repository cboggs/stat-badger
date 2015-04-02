import argparse
import json
import logging
import sys

sys.path.append("common")

from BadgerConfig import BadgerConfig
from BadgerLogger import BadgerLogger

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-f', '--config', help="Config file to load")
    args = argparser.parse_args()

    if not args.config:
        print "Could not load module 'telepathy'.\nPlease specify a configuration file via -f"
        exit(1)

    config = BadgerConfig(args.config).get_config_dict()
    #logger = BadgerLogger(logLevel=config['core']['log']['level'])
    logger = BadgerLogger(logLevel="debug")
    log = logger.logJSON
    print config['core']['log']['level']
    logger.getLogLevel()

    log("debug", blasphemy="sup yo?!", embeddedDict=config)

if __name__ == "__main__":
    main()
