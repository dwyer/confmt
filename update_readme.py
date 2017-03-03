#!/usr/bin/env python

import simpleconf as conf

with open('README.rst', 'w') as fp:
    fp.write(conf.__doc__.replace("'''", '"""'))
