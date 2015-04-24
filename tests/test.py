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
content = None

def compare(a, b):
    assert a == b, 'no match: %s' % '\n'.join(map(str, (a, b)))

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
    compare(baseenv, env)
    content = sorted(conf.dumps(env).splitlines())

# test object_hook
with open(CONFIG_FILENAME) as f:
    env = conf.load(f, object_hook=collections.OrderedDict)
    assert isinstance(env, collections.OrderedDict)
    compare(baseenv, env)
    compare(content, sorted(conf.dumps(env).splitlines()))

# test parse_int/float
with open(CONFIG_FILENAME) as f:
    env = conf.load(f, parse_int=str, parse_float=str)
    tempenv = baseenv.copy()
    tempenv['int'] = str(tempenv['int'])
    tempenv['float'] = str(tempenv['float'])
    compare(env, tempenv)
    compare(content, sorted(conf.dumps(env).splitlines()))

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
    compare(content, sorted(conf.dumps(env).splitlines()))

# test true/false/none tokens
with open(CONFIG_FILENAME) as f:
    s = f.read()
    s = s.replace('true', 'yes')
    s = s.replace('false', 'no')
    s = s.replace('null', 'none')
    env = conf.loads(s, true_token='yes', false_token='no', none_token='none')
    compare(env, baseenv)
    compare(content, sorted(conf.dumps(env).splitlines()))

# test comment_token
with open(CONFIG_FILENAME) as f:
    s = f.read().replace('#', ';')
    env = conf.loads(s, comment_token=';')
    compare(env, baseenv)
    compare(content, sorted(conf.dumps(env).splitlines()))

# test assignment_operator
with open(CONFIG_FILENAME) as f:
    s = '\n'.join(line.replace('=', ':', 1) for line in f)
    env = conf.loads(s, assignment_operator=':')
    compare(env, baseenv)
    compare(content, sorted(conf.dumps(env).splitlines()))

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
    compare(env, tempenv)
    compare(content[1:], sorted(conf.dumps(env).splitlines()))
