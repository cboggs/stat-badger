import json
import os
import re
import sys

sys.path.append("common")

from BadgerLogger import BadgerLogger

class BadgerConfig:

    def __init__(self, config_filename):
        self.log = BadgerLogger().logJSON

        comment_re = re.compile(
            '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
            re.DOTALL | re.MULTILINE
        )

        if not os.path.isfile(config_filename):
            print "Could not find configuration file {0}. Exiting.".format(config_filename)
            exit(1)

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
            print "Failed to load config, invalid JSON:"
            print "  {0}".format(e)
            exit(1)

        self.config_sanity_check()

    def config_sanity_check(self):
        if not "core" in self.config_data:
            print "missing \"core\" config section. Exiting."
            exit(1)

        for val in ["base_interval"]:
            if not val in self.config_data['core']:
                print "missing required \"{0}\" config value. Exiting.".format(val)
                exit(1)

    def get_config_dict(self):
        return self.config_data

def main():
    config = BadgerConfig("config.json")

if __name__ == "__main__":
    main()
