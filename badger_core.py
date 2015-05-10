import argparse
import copy
import copy_reg
from datetime import datetime as dt
import json
import logging
import os
from Queue import Queue
import re
import sys
import threading
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

        try:
            self.config = BadgerConfig(args.config).get_config_dict()
        except:
            import traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            print "Could not load config! Exiting!"
            exit(1)
            
        self.core_conf = self.config['core']
        self.log_conf = self.config['core']['log']
        self.sysinfo = {
            "datacenter": self.core_conf['datacenter'],
            "region": self.core_conf['region'],
            "zone": self.core_conf['zone'],
            "cluster": self.core_conf['cluster'],
            "hostname": self.core_conf['hostname'],
            "ipv4": self.core_conf['ipv4'],
            "ipv6": self.core_conf['ipv6']
        }
        self.logger = BadgerLogger(self.log_conf['level'], self.log_conf['dest'], self.log_conf['fileName'])
        self.log = self.logger.logJSON

        self.log("debug", message="BadgerCore initialization complete!")

        # this is passed to get_stats() in all modules (async and serial)
        #  and to emit_stats() in all emitters to enable per-module and
        #  per-emitter collection & emission intervals
        self.global_iteration = 0

        for item_type in ['modules', 'async_modules', 'emitters']:
            dir = self.config[item_type]['dir']
            if os.path.isdir(dir):
                sys.path.append(dir)
            else:
                self.log("err", msg="Can't find {0} dir at {1}. Exiting.".format(item_type, dir))
                exit(1)

        self.modules = [self.load_item(item, "modules") for item in self.config['modules']['included_modules']]

        self.async_modules = [self.load_item(item, "async_modules") for item in self.config['async_modules']['included_modules']]

        if (not self.modules or not self.modules[0]) and (not self.async_modules or not self.async_modules[0]):
            self.log("err", msg="No modules loaded! Exiting.")
            exit(1)

        self.emitters = [self.load_item(item, "emitters") for item in self.config['emitters']['included_emitters']]

        if not self.emitters[0]:
            self.log("err", msg="No emitters loaded! Exiting.")
            exit(1)

        # this queue will hold stats gathered by async modules. this
        #  allows async modules to take as long as they please while
        #  gathering stats, and the main loop will slurp them out of
        #  the queue in the next global iteration
        self.async_stats_queue = Queue(100000)

        # set a limit for items to retrieve from the async stats queue on each
        #  collection so as to (hopefully) avoid blocking the queue for too
        #  long in the event that things back up a bit
        self.queue_batch_size = 1000

        # set up one worker thread for each async_module included in
        #  the config
        self.async_workers = []

        for async_module in self.async_modules:
            worker = threading.Thread(target = self.collect_async_stats, args = (async_module,))
            worker.setDaemon(True)
            self.async_workers.append(worker)
        

    def load_item(self, item, item_type):
        required_methods = {
            'modules' : [ "get_stats" ],
            'async_modules' : [ "get_stats" ],
            'emitters' : [ "emit_stats" ]
        }

        base_item_config = os.path.join(self.config[item_type])
        item_dir = base_item_config['dir']
        config_dir = base_item_config['config']

        if not os.path.isfile(os.path.join(item_dir, item + ".py")):
            self.log("err", msg="Could not find {0} '{1}' in dir '{2}', skipping.".format(item_type, item, item_dir))
            return None

        if not os.path.isfile(os.path.join(config_dir, item + ".conf")):
            self.log("err", msg="Could not find config for {0} '{1}' in dir '{2}', skipping.".format(item_type, item, item_dir))
            return None
            

        try:
            loaded_item = __import__(item, [item])
        except:
            ei = sys.exc_info()
            self.log("error", msg="Could not load {0} '{1}' at {2}".format(item_type, item, os.path.join(item_dir, item + '.py')), exceptionType="{0}".format(str(ei[0]).split("'")[1]), exception="{0}".format(ei[1]))
            del ei
            return None

        try:
            item_config = BadgerConfig(os.path.join(config_dir, item + ".conf")).get_config_dict()
        except:
            self.log("err", msg="Could not load config for {0} '{1}'. Removing '{1}'.".format(item_type, item))
            return None

        self.log("debug", msg="Loaded config for {0} '{1}'".format(item_type, item))
        self.log("debug", msg="Successfully loaded {0} '{1}'.".format(item_type, item))


        item_name = str(loaded_item).split("'")[1]

        try:
            initialized_item = getattr(loaded_item, item_name)(item_config, self.log)
        except:
            ei = sys.exc_info()
            self.log("err", msg="Could not initialize {0} '{1}'".format(item_type, item_name), exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])))
        else:
            method_check_pass = True
            for method in required_methods[item_type]:
                if not hasattr(initialized_item, method):
                    self.log("err", msg="Required method '{0}' does not exist in {1} '{2}'. Unloading {1}.".format(method, item_type, str(item_name)), event="ModuleUnload")
                    method_check_pass = False
                    break

                if method_check_pass:
                    self.log("debug", msg="Successfully initialized {0} '{1}'".format(item_type, item_name))

        return initialized_item


    def collect_async_stats(self, module):
        while True:    
            payload = module.get_stats(self.global_iteration)

            if payload:
                for stat in payload:
                    self.async_stats_queue.put(stat)

            time.sleep(1)


    def collect_stats(self):
        # make sure we don't end up adding to the sysinfo dict and passing around
        #  a full payload on every run
        payload = copy.deepcopy(self.sysinfo)

        retrieved_from_queue = 0

        payload['timestamp'] = time.time()
        payload['points'] = []

        for module in self.modules:
            start = dt.now()
            try:
                stats_raw = module.get_stats(self.global_iteration)
            except:
                ei = sys.exc_info()
                module_name = str(module).split("<")[1].split(".")[0]
                self.log("err", msg="Exception encountered calling {0}.get_stats()".format(module_name), exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])), module=module_name)
                del ei, module_name
            else:
                if stats_raw:
                    elapsed_time = (dt.now() - start)
                    self.log("debug", msg="Elapsed time for module {0} gather: {1}".format(module, elapsed_time))
                    for measurement in stats_raw:
                        payload['points'].append(measurement)

        if self.async_stats_queue.qsize():
            while retrieved_from_queue < self.queue_batch_size:
                try:
                    payload['points'].append(self.async_stats_queue.get_nowait())
                except:
                    break
                else:
                    self.async_stats_queue.task_done()

        if not payload['points']:
            self.log("debug", msg="No stats gathered for global_iteration {0}".format(self.global_iteration))
            return None

        return payload


    def emit_stats(self, payload):
        if not payload:
            self.log("debug", msg="No stats to emit for global_iteration {0}".format(self.global_iteration))
            return

        # emission is async from the main loop, so that we can more reliably retain
        #  a one-second base polling interval
        for emitter in self.emitters:
            t = threading.Thread(target=emitter.emit_stats, args=(payload,self.global_iteration))
            t.start()


    def dig(self):
        for worker in self.async_workers:
            worker.start()

        while True:
            start_dig = dt.now()
            self.log("debug", msg="Active threads: {0}".format(threading.activeCount()))
            start_collect = dt.now()
            payload = self.collect_stats()
            end_collect = dt.now()

            self.log("debug", msg="Emitting stats")

            start_emit = dt.now()
            self.emit_stats(payload)
            end_emit = dt.now()

            self.log("debug", msg="Elapsed time for collection: {0}".format((end_collect - start_collect).total_seconds()))
            self.log("debug", msg="Elapsed time for emission: {0}".format((end_emit - start_emit).total_seconds()))

            # need to be sure we roll over this counter appropriately, otherwise we're
            #  guaranteed a crash every 292471208677.53-ish years. that would suck.
            if self.global_iteration == sys.maxint:
                self.global_iteration = 0
            else:
                self.global_iteration += 1

            elapsed_dig_time = (dt.now() - start_dig).total_seconds()
            adjusted_sleep_time = float(1 - elapsed_dig_time)
            self.log("debug", msg="Elapsed dig time: {0} -- Sleeping for {1} seconds".format(elapsed_dig_time, adjusted_sleep_time))

            time.sleep(adjusted_sleep_time)

if __name__ == "__main__":
    try:
        badger = Badger()
    except:
        import traceback
        ei = sys.exc_info()
        traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
        print "Could not initialize Badger Core! Exiting."
        exit(1)

    badger.dig()
