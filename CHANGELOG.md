## v0.1.5 [2015-05-19]
### Features
- [#10] (https://github.com/cboggs/stat-badger/pull/10): add thread counts to per-process stats in process_stats module

### Bugfixes
- [#4] (https://github.com/cboggs/stat-badger/issues/4): load_item method throws exception and kills stat badger when any module or emitter fails to initialize
- [#6] (https://github.com/cboggs/stat-badger/issues/6): badger_core crashes when main loop takes >= 1.0s to execute
- [#8] (https://github.com/cboggs/stat-badger/issues/8): process_stats module does not collect ALL context switches for a process


## v0.1.4 [2015-05-09]

### Features
- [#1] (https://github.com/cboggs/stat-badger/issues/1): Support for async stats collection

### Bugfixes
- [#2] (https://github.com/cboggs/stat-badger/issues/2): No output to stderr when anything fails inside main Badger object
