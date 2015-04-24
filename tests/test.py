#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import collections
import os
import re
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(TESTS_DIR)
CONFIG_FILENAME = os.path.join(TESTS_DIR, 'test.conf')

sys.path.append(PARENT_DIR)

import simpleconf as conf

baseenv = None

def compare(a, b):
    for (var1, val1), (var2, val2) in zip(sorted(a.items()),
                                          sorted(b.items())):
        assert var1 == var2, (val1, var2)
        assert val1 == val2, (val1, val2)
    return True

# test defaults
with open(CONFIG_FILENAME) as f:
    env = conf.load(f)
    baseenv = env
    assert env['string'] == '中國 = 中国'
    assert env['int'] == -42
    assert env['float'] == 3.14
    assert env['yes'] is True
    assert env['no'] is False
    assert env['none'] is None
    assert env[''] == ''
    assert compare(baseenv, env)

# test object_hook
with open(CONFIG_FILENAME) as f:
    env = conf.load(f, object_hook=collections.OrderedDict)
    assert isinstance(env, collections.OrderedDict)
    assert compare(baseenv, env)

# test parse_int/float
with open(CONFIG_FILENAME) as f:
    env = conf.load(f, parse_int=str, parse_float=str)
    tempenv = baseenv.copy()
    tempenv['int'] = str(tempenv['int'])
    tempenv['float'] = str(tempenv['float'])
    assert compare(env, tempenv)

# test parse_*
with open(CONFIG_FILENAME) as f:
    env = conf.load(f, parse_int=float, parse_float=lambda x: int(float(x)))
    assert isinstance(env['int'], float)
    assert isinstance(env['float'], int)
    tempenv = baseenv.copy()
    tempenv['int'] = float(tempenv['int'])
    tempenv['float'] = int(tempenv['float'])

# test true/false/none tokens
with open(CONFIG_FILENAME) as f:
    env = conf.load(f, true_token=None, false_token=None, none_token=None)
    tempenv = baseenv.copy()
    tempenv['yes'] = 'true'
    tempenv['no'] = 'false'
    tempenv['none'] = 'null'

# test true/false/none tokens
with open(CONFIG_FILENAME) as f:
    s = f.read()
    s = s.replace('true', 'yes')
    s = s.replace('false', 'no')
    s = s.replace('null', 'none')
    env = conf.loads(s, true_token='yes', false_token='no', none_token='none')
    assert compare(env, baseenv)

# test comment_token
with open(CONFIG_FILENAME) as f:
    s = f.read().replace('#', ';')
    env = conf.loads(s, comment_token=';')
    assert compare(env, baseenv)

# test assignment_operator
with open(CONFIG_FILENAME) as f:
    s = '\n'.join(line.replace('=', ':', 1) for line in f)
    env = conf.loads(s, assignment_operator=':')
    assert compare(env, baseenv)

# test strict_mode
with open(CONFIG_FILENAME) as f:
    true = False
    try:
        conf.load(f, strict_mode=True)
    except ValueError:
        true = True
    assert true

# test variable_validator
with open(CONFIG_FILENAME) as f:
    env = conf.load(f,
                    variable_validator=lambda s: re.match(r'[\w_][\w\d_]*', s))
    tempenv = baseenv.copy()
    del tempenv['']
    assert compare(env, tempenv)
