Each emitter is run in an untracked async thread by Badger Core at every global polling interval (1s). Effectively, emitters are expected to be used in a fire-and-forget fashion (though they can still log events just fine). Doing this keeps slow emission from impacting the global polling cycle and causing inconsistent granularities in the back-ends you choose. 


Emitters are required to consist of the following:
    * a python file in your emitter directory: `youremitter.py`
    * a config file named the same as your emitter, but with a '.conf' suffix, in your emitter config directory: `youremitter.conf`

The emitter needs to define a class that conforms to the requirements:
    * has the same name as the base filename: `class youremitter(object):`
    * constructor accepts the following:
        - a config dictionary object (pretty much arbitrary contents)
        - a BadgerLogger object (for that sweet, sweet structured log output)
    * has at least one method, named "emit_stats", which accepts two args:
        * a payload dictionary object (see project README for format)
        * an int that acts as the global iteration counter

Beyond that, you're free to do whatever you need to emit the stats. The config you accept doesn't have to contain any particular values, just needs to be marshal-able JSON (even if it's just {}).

Badger Core is designed to allow you to implement custom intervals in your emitters, if you'd like. You can see an example of how to do so in any of the stock modules, such as [stdout_pretty.py](https://github.com/cboggs/stat-badger/blob/master/badger_emitters/stdout_pretty.py).

You are also free to implement stat blacklisting in your emitters, though there is no expectation that a blacklist will exist. It's worth noting, however, that blacklisting a stat at the module level is **not** a global blacklisting of that stat - it will simply be omitted from that particular emitter's output. If you need to globally blacklist a stat, you should do so in the appropriate module configuration.

Please also note that blacklist and custom interval handling is left entirely up to you - there is no core handling of those concepts.
