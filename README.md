[![PyPI](https://img.shields.io/pypi/v/pyexos.svg)](https://pypi.python.org/pypi/pyEXOS)
[![PyPI](https://img.shields.io/pypi/dm/pyexos.svg)](https://pypi.python.org/pypi/pyEXOS)
[![Build Status](https://travis-ci.org/LINXNet/pyexos.svg?branch=master)](https://travis-ci.org/LINXNet/pyexos)
[![Coverage Status](https://coveralls.io/repos/github/LINXNet/pyexos/badge.svg?branch=master)](https://coveralls.io/github/LINXNet/pyexos?branch=master)


# pyEXOS

Python library to manage Extreme Networks devices running EXOS

## Requirements

### Python
* netmiko >= 1.4.0

### Extreme Networks
* EXOS version == 16.2

## Install

### Install via pip
```bash
pip install pyEXOS
```

### Upgrade via pip
```bash
pip install --upgrade pyEXOS
```

## Documentation

### Connect to remote device
```python
>>> from pyEXOS import EXOS
>>> device = EXOS(hostname='192.168.1.222', username='admin', password='admin', port=22, timeout=10)
>>> device.open()
```

### Load and later discard config
```python
>>> device.load_candidate_config(config='configure snmp sysName test-string')
>>> print device.candidate_config
>>> ['configure snmp sysName test-string']
>>> device.discard_config()
>>> print device.candidate_config
>>> None
```

### Retreive running config from the device
```python
>>> device.get_running_config()
>>> print device.running_config
>>> [u'...']
```

###  Load, diff merge, commit merge config and later roll back to previous state
```python
>>> device.load_candidate_config(filename='config_merge.txt')
>>> diff = device.compare_merge_config()
>>> print diff
>>> --- running_config.conf
+++ candidate_config.conf
@@ -22,0 +23 @@
+configure snmp sysName test-merge-file
>>> device.commit_config()
```

###  Load, diff replace, commit replace config and later roll back to previous state
```python
>>> device.load_candidate_config(filename='config_replace.txt')
>>> diff = device.compare_replace_config()
>>> print diff
...
>>> device.commit_replace_config()
>>> device.rollback()
```

### Close the connection
```python
>>> device.close()
```

## License

Copyright 2017 LINX

Licensed under the Apache License, Version 2.0: http://www.apache.org/licenses/LICENSE-2.0
