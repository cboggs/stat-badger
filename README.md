# Stat Badger - Commodify Your Stats
Stat Badger is a tool to commodify system stats. It makes zero assumptions about what stats you want to gather, and zero assumptions about where you want to send those stats.

## The Basics
Badger is intended to be run on every (Linux) host you could possibly want to gather stats from. It consists of the Badger Core, Modules, and Emitters. It collects metrics from all modules and emits (asynchronously) from all emitters on a 1 second interval. You can configure custom intervals on both a per-module and per-emitter basis. You can also blacklist stats at the module and emitter level. (More detail on custom intervals and blacklists in the module and emitter README files).

The stock file and directory structure is as follows (though module and emitter dirs are configurable):
- stat-badger-0.2.0
    - badger_core.py
    - common (classes that badger_core, modules, and emitters rely on)
    - badger_modules
        - cpu.py
        - conf.d
            - cpu.conf
    - badger_emitters
        - influxdb08_emitter.py
        - conf.d
            - influxdb08_emitter.conf


## Configuration
Badger expects a JSON configuration file, provided via the `-f` command-line argument. This file can contain comment lines / blocks (//, /* ... */)
See [config.json](https://github.com/cboggs/stat-badger/blob/master/config.json) as an example.


## Stats Format
Badger modules present stats as an array of simple dictionary objects, which are rolled up into a larger dictionary with some additional metadata about the host. Emitters accept this larger dictionary, and can chop it up for emission in any manner they choose.

### Example module output:
```
[
    {"cpu.user": {"value": 8, "units": "percent"}},
    {"cpu.ctxt_per_sec": {"value": 8, "units": ""}}
]
```

### Example emitter input:
```
{
    "datacenter": "EC2",
    "region":     "us-west-1"
    "zone":       "us-west-1a",
    "cluster":    "test-cluster-01",
    "hostname":   "test-node-01",
    "ipv4":       "10.10.10.2",
    "ipv6":       "",
    "timestamp":  1429628878,
    "points": [
        {"cpu.user": {"value": 8, "units": "percent"}},
        {"cpu.ctxt_per_sec": {"value": 8, "units": ""}}
    ]
}
```

The metadata above "points: [...]" is cobbled together by the Core and included in every payload. 

## Modules and Emitters
You are free to define your own 
You can get a pretty good idea of what it takes to create a module or emitter by looking at those that are included with Badger out of the box. For more detail, see [badger_modules/README.md](https://github.com/cboggs/stat-badger/blob/master/badger_modules/README.md) and [badger_emitters/README.md](https://github.com/cboggs/stat-badger/blob/master/badger_emitters/README.md).
