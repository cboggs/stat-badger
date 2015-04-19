import argparse
import copy
from datetime import datetime as dt
import json
import logging
from multiprocessing import Pool
import os
import re
import sys
import time

sys.path.append("common")

from BadgerConfig import BadgerConfig
from BadgerLogger import BadgerLogger

class Badger(object):
    def __init__(self):
        argparser = argparse.ArgumentParser()
        argparser.add_argument('-f', '--config', help="Config file to load")
        args = argparser.parse_args()

        if not args.config:
            print "Could not load module 'telepathy'.\nPlease specify a configuration file via -f"
            exit(1)

        self.config = BadgerConfig(args.config).get_config_dict()
        self.core_conf = self.config['core']
        self.sysinfo = {
            "datacenter": self.core_conf['datacenter'],
            "region": self.core_conf['region'],
            "zone": self.core_conf['zone'],
            "cluster": self.core_conf['cluster'],
            "hostname": self.core_conf['hostname'],
            "ipv4": self.core_conf['ipv4'],
            "ipv6": self.core_conf['ipv6']
        }
        self.logger = BadgerLogger(self.core_conf['log']['level'])
        self.log = self.logger.logJSON

        self.log("debug", message="BadgerCore initialization complete!")

        self.emitter_pool = Pool(processes=self.config['emitters']['workers'])

        self.loaded_modules_and_emitters = self.load_modules_and_emitters()
        self.initialized_modules_and_emitters = self.initialize_modules_and_emitters()
        self.modules = self.initialized_modules_and_emitters['modules']
        self.emitters = self.initialized_modules_and_emitters['emitters']

    def load_modules_and_emitters(self):
        found = {
            "emitters" : [],
            "modules"  : []
        }
        loaded = {
            "emitters" : [],
            "modules"  : [],
            "configs"  : {}
        }

        for item in ['modules', 'emitters']:
            dir = self.config[item]['dir']
            config = self.config[item]['config']
            if not os.path.isdir(dir):
                self.log("crit", msg="Could not find {0} directory '{1}'".format(item, dir), exiting=True)
                exit(1)

            if not os.path.isdir(config):
                self.log("crit", msg="Could not find {0} config directory '{1}'".format(item, config), exiting=True)
                exit(1)

            sys.path.append(dir)

            # Check to see if the modules and emitters desired are actually present in the right place
            for sub_item in self.config[item]['included_' + item]:
                if not os.path.isfile(os.path.join(dir, sub_item + ".py")):
                    self.log("err", msg="Could not find {0} '{1}' in dir '{2}', skipping.".format(item, sub_item, dir))
                else:
                    self.log("debug", msg="{0} '{1}' exists".format(item, sub_item))
                    found[item].append(sub_item)

            self.log("info", msg="Found {0} : {1}".format(item, found[item]))

            # Try to dynamically import all requested (and found) modules. We loop
            #  through these instead of using map(__import__, found_modules) in
            #  order to avoid failing some portion of the op on account of a single
            #  failed import. This also lets me tell you which module failed and why
            #  in a cleaner way
            for sub_item in found[item]:
               try:
                    loaded[item].append(__import__(sub_item, [sub_item]))
               except:
                    ei = sys.exc_info()
                    self.log("err", msg="Could not load {0} '{1}' at {2}".format(item, sub_item, os.path.join(dir, sub_item + '.py')), exceptionType="{0}".format(str(ei[0]).split("'")[1]), exception="{0}".format(ei[1]))
                    del ei
               else:
                    sub_item_config_file = os.path.join(config, sub_item + ".conf")
                   
                    try:
                        sub_item_config = BadgerConfig(sub_item_config_file).get_config_dict()
                    except:
                        loaded[item].pop()
                        self.log("err", msg="Could not load config for {0} '{1}'. Removing '{1}'.".format(item, sub_item))
                    else:
                        loaded['configs'][sub_item] = sub_item_config
                        self.log("debug", msg="Loaded config for {0} '{1}'".format(item, sub_item))
                        self.log("debug", msg="Successfully loaded {0} '{1}'.".format(item, sub_item))

            # Critical exit if no modules were loaded - no sense in spinning doing nothing
            if not len(loaded[item]):
                self.log("crit", msg="No {0} were loaded!".format(item), event="ErrExit")
                exit(1)

            self.log("info", msg="Loaded {0} : {1}".format(item, [str(si).split("'")[1] for si in loaded[item]]))

        return (loaded)


    def initialize_modules_and_emitters(self):
        initialized = {
            'modules'  : [],
            'emitters' : []
        }

        required_methods = {
            'modules' : [ "get_metrics" ],
            'emitters' : [ "emit_metrics" ],
        }

        for item in ['modules', 'emitters']:
            for sub_item in self.loaded_modules_and_emitters[item]:
                sub_item_name = str(sub_item).split("'")[1]
                sub_item_config = self.loaded_modules_and_emitters['configs'][sub_item_name]

                try:
                    initialized_item = getattr(sub_item, sub_item_name)(sub_item_config, self.log)
                except:
                    ei = sys.exc_info()
                    self.log("err", msg="Could not initialize {0} '{1}'".format(item, sub_item_name), exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])))
                else:
                    method_check_pass = True
                    for method in required_methods[item]:
                        if not hasattr(initialized_item, method):
                            self.log("err", msg="Required method '{0}' does not exist in {1} '{2}'. Unloading {1}.".format(method, item, str(sub_item).split("'")[1]), event="ModuleUnload")
                            method_check_pass = False
                            break

                        if method_check_pass:
                            initialized[item].append(initialized_item)
                            self.log("debug", msg="Successfully initialized {0} '{1}'".format(item, sub_item_name))

            if not len(initialized[item]):
                self.log("crit", msg="No {0} could be initialized!".format(item), event="ErrExit")
                exit(1)
            
            self.log("info", msg="Initialized {0}".format(item), initializedItems=[str(ie).split(".")[0].split("<")[1] for ie in initialized[item]])

        return initialized

    def collect_metrics(self):
        # make sure we don't end up adding to the sysinfo dict and passing around
        #  a full payload on every run
        payload = copy.deepcopy(self.sysinfo)

        payload['timestamp'] = time.time()
        payload['points'] = []

        for module in self.modules:
            start = dt.now()
            try:
                metrics_raw = module.get_metrics(self.core_conf['interval'])
            except:
                ei = sys.exc_info()
                module_name = str(module).split("<")[1].split(".")[0]
                self.log("err", msg="Exception encountered calling {0}.get_metrics()".format(module_name), exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])), module=module_name)
                del ei, module_name
            else:
                elapsed_time = (dt.now() - start)
                self.log("debug", msg="Elapsed time for module {0} gather: {1}".format(module, elapsed_time))
                for measurement in metrics_raw:
                    payload['points'].append(measurement)

        return payload


    def __call__(self, (emitter, payload)):
        self.run_emitter((emitter, payload))

    def run_emitter(self, (emitter, payload)):
        print "****************************{0}".format(payload)
        startEmit = dt.now()
        #emitter.emit_metrics(payload)
        endEmit = dt.now()
        self.log("debug", msg="Elapsed time for emission from emitter {0}: {1}".format(str(emitter).split(".")[1].split()[0], (endEmit - startEmit).total_seconds()))


    def emit_metrics(self, payload):
        self.emitter_pool.map(self, ((emitter, payload) for emitter in self.emitters))
#        for emitter in self.emitters:
#            self.run_emitter((emitter, payload))

    def dig(self):
        while True:
            startCollect = dt.now()
            payload = self.collect_metrics()
            endCollect = dt.now()

            try:
                json_metrics = json.dumps(payload)
            except:
                ei = sys.exc_info()
                self.log("err", msg="Exception encountered marshalling payload to JSON", exceptionType=str(ei[0]), exception=str(ei[1]))
            else:
                self.log("debug", msg="Emitting metrics")

            startEmit = dt.now()
            self.emit_metrics(payload)
            endEmit = dt.now()

            self.log("debug", msg="Elapsed time for collection: {0}".format((endCollect - startCollect).total_seconds()))
            self.log("debug", msg="Elapsed time for emission: {0}".format((endEmit - startEmit).total_seconds()))

            time.sleep(self.core_conf['interval'])

if __name__ == "__main__":
    badger = Badger()
    badger.dig()
