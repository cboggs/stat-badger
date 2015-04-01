import argparse
import json
import sys

sys.path.append("common")

from BadgerConfig import BadgerConfig

argparser = argparse.ArgumentParser()

argparser.add_argument('-d', '--debug', help="Set debug level - the higher the level, the further down the rabbit hole...")
argparser.add_argument('-f', '--config', help="Config file to load")

argparser.parse_args()
args = argparser.parse_args()

if not args.config:
    print "Could not load module 'telepathy'.\nPlease specify a configuration file via -f"
    exit(1)

def main():
    config = BadgerConfig(args.config).get_config_dict()

    print json.dumps(config)

if __name__ == "__main__":
    main()
