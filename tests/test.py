#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import collections
import os
import re
import sys

import simpleconf as conf

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(TESTS_DIR)
CONFIG_FILENAME = os.path.join(TESTS_DIR, 'test.conf')

sys.path.insert(0, PARENT_DIR)

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

# test object_type
with open(CONFIG_FILENAME) as f:
    env = conf.load(f, object_type=collections.OrderedDict)
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
    env = conf.load(f, keywords={})
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
    env = conf.loads(s, keywords={'yes': True, 'no': False, 'none': None})
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
        conf.load(f, strict=True)
    except ValueError:
        true = True
    assert true

# test key_validator
with open(CONFIG_FILENAME) as f:
    env = conf.load(f, key_validator=lambda s: re.match(r'[\w_][\w\d_]*', s))
    tempenv = baseenv.copy()
    del tempenv['']
    compare(env, tempenv)
    compare(content[1:], sorted(conf.dumps(env).splitlines()))

    def valid(s):
        return ' ' not in s

    env = conf.loads('a.b = 1 \n a.b.c d = 2', key_separator='.',
                     key_validator=valid)
    assert env['a']['b'] == 1
    env = conf.loads('a.b c.d = 1', key_separator='.', key_validator=valid)
    assert not env

# test key_separator
with os.popen('git config --list --local') as f:
    env = conf.load(f, key_separator='.', parse_int=float)
    opts = dict(key_separator='->', keywords={'yes': True, 'no': False})
    s = conf.dumps(env, **opts)
    compare(env, conf.loads(s, **opts))

# test escape_token
s = 'a \= b = \#t # this should be #t'
keywords = {'#t': True, '#f': False}
obj = conf.loads(s, keywords=keywords)
assert 'a = b' in obj and obj['a = b'] is True, obj
t = conf.dumps({'a = b': True}, keywords=keywords)
assert s.startswith(t), (s, t)

obj = conf.loads('a.b = \#t \n a\.b = \#f', keywords=keywords,
                 key_separator='.')
assert 'a' in obj and 'b' in obj['a'] and obj['a']['b'] is True, obj
assert 'a.b' in obj and obj['a.b'] is False, obj
