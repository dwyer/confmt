#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import collections
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(TESTS_DIR)
CONFIG_FILENAME = os.path.join(TESTS_DIR, 'test.conf')

sys.path.append(PARENT_DIR)

import confmt

# test defaults
with open(CONFIG_FILENAME) as f:
    env = confmt.load(f)
    assert env['string'] == '中國 = 中国'
    assert env['int'] == -42
    assert env['float'] == 3.14
    assert env['yes'] is True
    assert env['no'] is False
    assert env['none'] is None
    assert env[''] == ''

# test object_hook
with open(CONFIG_FILENAME) as f:
    env = confmt.load(f, object_hook=collections.OrderedDict)
    assert isinstance(env, collections.OrderedDict)

# test parse_int/float
with open(CONFIG_FILENAME) as f:
    env = confmt.load(f, parse_int=str, parse_float=str)
    assert env['string'] == '中國 = 中国'
    assert env['int'] == '-42'
    assert env['float'] == '3.14'
    assert env['yes'] is True
    assert env['no'] is False
    assert env['none'] is None
    assert env[''] == ''

# test parse_*
with open(CONFIG_FILENAME) as f:
    env = confmt.load(f, parse_int=float, parse_float=lambda x: int(float(x)))
    assert isinstance(env['int'], float)
    assert env['string'] == '中國 = 中国'
    assert env['int'] == -42.0
    assert env['float'] == 3
    assert env['yes'] is True
    assert env['no'] is False
    assert env['none'] is None
    assert env[''] == ''

# test true/false/none tokens
with open(CONFIG_FILENAME) as f:
    env = confmt.load(f, true_token=None, false_token=None, none_token=None)
    assert env['string'] == '中國 = 中国'
    assert env['int'] == -42
    assert env['float'] == 3.14
    assert env['yes'] == 'true'
    assert env['no'] == 'false'
    assert env['none'] == 'null'
    assert env[''] == ''

# test true/false/none tokens
env = confmt.loads('none = none\nyes = yes\nno = no', true_token='yes',
                   false_token='no', none_token='none')
assert env['yes'] is True
assert env['no'] is False
assert env['none'] is None

# test comment_token
env = confmt.loads('# = 1\n; = 2', comment_token=';')
assert env['#'] == 1
assert ';' not in env

# test assignment_operator
env = confmt.loads('one: 1\ntwo: 2\n', assignment_operator=':')
assert env['one'] == 1
assert env['two'] == 2

# test strict_mode
true = False
try:
    confmt.loads('error', strict_mode=True)
except ValueError:
    true = True
assert true

# test variable_validator
env = confmt.loads('one_love = 1\ntwo doves = 2',
                   variable_validator=lambda s: ' ' not in s)
assert env['one_love'] == 1
assert 'two doves' not in env
