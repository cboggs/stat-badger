**WARNING:** If your modules cannot run quickly (as in, "a handful of milliseconds" quickly), then you should include them in your config as *async* modules, not "normal" modules. Badger Core is wired for a 1-second polling interval, and exceeding that boundary due to slow synchronous modules will cause erratic granularities in your back-ends. This is smoothed a bit by adjusting the sleep interval to account for elapsed collection/emission time, but either way you should strive to chew up as little of that 1000 milliseconds as you possibly can.

Generally, each module should be responsible for a single component of the system. For example, Stat Badger ships with a cpu module, network module, etc. Useful additions would be an apache2 module, a MongoDB module, etc.

All modules that meet the requirements below can be used as *either* syncrhonous or asynchronous modules. The deciding factor regarding how you load any given module is simply the potential worst-case scenario for execution time of the module's get_stats() method. As a rule of thumb: modules that read from /proc are crazy fast and are good candidates for synchronous modules, while modules that query APIs or have to deal with any other delay-prone data source should be loaded as asynchronous modules so as to avoid impacting the global polling interval adversely.

Modules are required to consist of the following:
    * a python file in your module directory: `yourmod.py`
    * a config file named the same as your module, but with a '.conf' suffix, in your module config directory: `yourmod.conf`

The module needs to define a class that conforms to the requirements:
    * has the same name as the base filename: `class yourmod(object):`
    * constructor accepts the following:
        - a config dictionary object (pretty much arbitrary contents)
        - a BadgerLogger object (for that sweet, sweet structured log output)
    * has at least one method, named "get_stats", which accepts an int that acts as the global iteration counter
    * get_stats() must return an array of dictionaries as such:
        ```
        [
            {"cpu.user": {"value": 8, "units": "percent"}},
            {"cpu.ctxt_per_sec": {"value": 8, "units": ""}}
        ]
        ```

Beyond that, you're free to do whatever you need to gather the stats. The config you accept doesn't have to contain any particular values, just needs to be marshal-able JSON (even if it's just {}).

Badger Core is designed to allow you to implement custom intervals in your modules, if you'd like. You can see an example of how to do so in any of the stock modules, such as [load.py](https://github.com/cboggs/stat-badger/blob/master/badger_modules/load.py).

You are also free to implement stat blacklisting in your modules, though there is no expectation that a blacklist will exist. It's worth noting, however, that blacklisting a stat at the module level is effectively a **GLOBAL** blacklisting of that stat. If you want to keep a particular stat from reaching a particular back-end, you should blacklist it in the appropriate emitter configuration.

Please also note that blacklist and custom interval handling is left entirely up to you - there is no core handling of those concepts.
