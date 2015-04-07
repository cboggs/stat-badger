import argparse
from datetime import datetime as dt
import json
import logging
import os
import re
import sys

sys.path.append("common")

from BadgerConfig import BadgerConfig
from BadgerLogger import BadgerLogger

def load_modules(module_dir, config_dir, modules_requested, log):
    found_modules = []
    loaded_modules = []

    if not os.path.isdir(module_dir):
        log("crit", msg="Could not find module_dir '{0}'".format(module_dir), exiting=True)
        exit(1)

    if not os.path.isdir(config_dir):
        log("crit", msg="Could not find config_dir '{0}'".format(config_dir), exiting=True)
        exit(1)

    sys.path.append(module_dir)

    # Check to see if the modules desired are actually present in the right place
    for module in modules_requested:
        if not os.path.isfile(os.path.join(module_dir, module + ".py")):
            log("err", msg="Could not find module '{0}' in module_dir '{1}', skipping.".format(module, module_dir))
        else:
            log("debug", msg="Module '{0}' exists".format(module))
            found_modules.append(module)

    log("debug", msg="Found modules: {0}".format(found_modules))

    # Try to dynamically import all requested (and found) modules. We loop
    #  through these instead of using map(__import__, found_modules) in
    #  order to avoid failing some portion of the op on account of a single
    #  failed import. This also lets me tell you which module failed and why
    #  in a cleaner way
    for module in found_modules:
       try:
            loaded_modules.append(__import__(module, [module]))
       except:
            ei = sys.exc_info()
            log("err", msg="Could not load module '{0}' at {1}".format(module, os.path.join(module_dir, module + '.py')), exceptionType="{0}".format(str(ei[0]).split("'")[1]), exception="{0}".format(ei[1]))
            del ei
       else: log("debug", msg="Successfully loaded module '{0}'".format(module))

    # Critical exit if no modules were loaded - no sense in spinning doing nothing
    if not len(loaded_modules):
        log("crit", msg="No modules were loaded!", event="ErrExit")
        exit(1)

    return loaded_modules

def initialize_modules(loaded_modules, log):
    initialized_modules = []

    for module in loaded_modules:
        module_name = str(module).split("'")[1]
        try:
            im = getattr(module, module_name)(log)
        except:
            ei = sys.exc_info()
            log("err", msg="Could not initialize module '{0}'".format(module_name), exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])))
        else:
            if hasattr(im, "get_metrics"):
                initialized_modules.append(im)
            else:
                log("err", msg="Required method 'get_metrics' does not exist in module '{0}'. Unloading module.".format(str(module).split("'")[1]), event="ModuleUnload")

    if not len(initialized_modules):
        log("crit", msg="No modules could be initialized!", event="ErrExit")
        exit(1)

    return initialized_modules

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-f', '--config', help="Config file to load")
    args = argparser.parse_args()

    if not args.config:
        print "Could not load module 'telepathy'.\nPlease specify a configuration file via -f"
        exit(1)

    config = BadgerConfig(args.config).get_config_dict()
    logger = BadgerLogger(config['core']['log']['level'])
    log = logger.logJSON
    payload = []

    log("debug", message="BadgerCore initialization complete!")

    modules = initialize_modules(load_modules(config['modules']['module_dir'], config['modules']['config_dir'], config['modules']['modules_to_load'], log), log)

    for module in modules:
        start = dt.now()
        try:
            metrics_raw = module.get_metrics()
        except:
            ei = sys.exc_info()
            module_name = str(module).split("<")[1].split(".")[0]
            log("err", msg="Exception encountered calling {0}.get_metrics()".format(module_name), exceptionType="{0}".format(str(ei[0])), exception="{0}".format(str(ei[1])), module=module_name)
            del ei, module_name
        else:
            elapsed_time = (dt.now() - start)
            log("debug", msg="Elapsed time for module {0} gather: {1}".format(module, elapsed_time))
            for measurement in metrics_raw:
                payload.append(measurement)

    try:
        marshaled_metrics = json.dumps(payload)
    except:
        ei = sys.exc_info()
        log("err", msg="Exception encountered marshalling payload to JSON", exceptionType=str(ei)[0], exception=str(ei)[1])

if __name__ == "__main__":
    main()
