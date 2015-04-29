import json
import os
import re
import sys

class BadgerConfig:

    def __init__(self, config_filename):

        comment_re = re.compile(
            '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
            re.DOTALL | re.MULTILINE
        )

        if not os.path.isfile(config_filename):
            raise Exception("Could not find configuration file {0}. Exiting.".format(config_filename))

        try:
            with open(config_filename) as f:
                content = ''.join(f.readlines())
                match = comment_re.search(content)
                while match:
                    content = content[:match.start()] + content[match.end():]
                    match = comment_re.search(content)
                self.config_data = json.loads(content)
                f.close()

        except ValueError as e:
            raise Exception("Could not load configuration file {0}. Exiting.".format(config_filename))

    def get_config_dict(self):
        return self.config_data

def main():
    import argparse

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-f', '--config', help="Config file to load")
    args = argparser.parse_args()

    if not args.config:
         print "FAILED: Please specify a configuration file via -f"
         exit(1)

    config = BadgerConfig(args.config).get_config_dict()
    print json.dumps(config, sort_keys=True, indent=4, separators=(',', ': '))

if __name__ == "__main__":
    main()
