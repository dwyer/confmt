#!/usr/bin/env python

import simpleconf as conf

with open('README', 'w') as fp:
    fp.write(conf.__doc__)
