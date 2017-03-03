simpleconf is a very simple and easy data-interchange format for
configuration files. It's a subset of JSON, supporting everything but arrays,
but with significantly simpler syntax.

Audience
========

Developers who need a user-facing configuration file format that's easy to read
and write, who don't need arrays so may therefore exchange the power of JSON or
YAML for a much simpler, almost syntax-free format.

Format Syntax
=============

    * A statement is a key/value pair separated by an assignment operator (= by
      default).
    * A comment is any line that begins with a comment token (# by default).
    * Integers, real numbers, and the keywords "true", "false" and "null" are
      evaluated by default.
    * All syntax and keywords can be changed or removed (except the assignment
      operator, which can only be changed).
    * Support for nested objects/environments is optional.

Deserialization
===============

Note: The following examples apply to the ``ConfDecoder``, ``load`` and
``loads`` class and functions.

    >>> import simpleconf as conf
    >>> conf.loads("""
    ...
    ... # this is a comment
    ...
    ... # the following is a statement
    ... energy = mass times the speed of light squared
    ...
    ... """)
    {'energy': 'mass times the speed of light squared'}

Only the first assignment operator is evaluated.

    >>> conf.loads('relativity = e = mc^2')
    {'relativity': 'e = mc^2'}

Numbers, booleans and "null" evaluate to their primitive counterparts.

    >>> conf.loads("""
    ...
    ... answer = 42
    ... phish = 1.618
    ... yes = true
    ... no = false
    ... maybe = null
    ...
    ... """)
    {'answer': 42, 'maybe': None, 'yes': True, 'phish': 1.618, 'no': False}

Key names evaluate to strings and can contain any character except the
assignment operator.

    >>> conf.loads("""
    ...
    ... two birds = 2
    ... one stone = 1
    ... three's a "crowd"? = true
    ...
    ... """)
    {'one stone': 1, 'two birds': 2, 'three's a "crowd"?': True}

The deserialized object is a ``dict`` by default, but can be configured with
the ``object_type`` argument. For example, you could use an OrderedDict to
preserve the order.

    >>> import collections
    >>> conf.loads("""
    ...
    ... one = 1
    ... two = 2
    ... tree = 3
    ...
    ... """, object_type=collections.OrderedDict)
    OrderedDict([(u'one', 1), (u'two', 2), (u'tree', 3)])

Numbers are deserialized to ``int`` and ``float`` by default, but can be
configured with the ``parse_int`` and ``parse_float`` arguments.

    >>> import decimal
    >>> conf.loads("""
    ...
    ... answer = 42
    ... phish = 1.618
    ...
    ... """, parse_int=float, parse_float=decimal.Decimal)
    {'answer': 42.0, 'phish': Decimal('1.618')}

Syntax Configuration
====================

Note: the following examples apply to all classes and functions.

The assignment operator can be overloaded with the ``assignment_operator``
argument.

    >>> conf.loads("""
    ...
    ... a: 1
    ... b: 52
    ... this = key: value
    ...
    ... """, assignment_operator=':')
    {'a': 1, 'this = key': 'value', 'b': 52}

    >>> print conf.dumps(_, assignment_operator=':')
    a : 1
    this = key : value
    b : 52

The keywords corresponding to ``True``, ``False`` and ``None`` can be overloaded
with the ``keywords`` argument to ``load`` and ``loads``.

    >>> keywords = {'yes': True, 'no': False, 'none': None}
    >>> conf.loads("""
    ...
    ... yep = yes
    ... nah = no
    ... meh = none
    ...
    ... """, keywords=keywords)
    {'yep': True, 'nah': False, 'meh': None}
    >>> print conf.dumps(_, keywords=keywords)
    yep = yes
    nah = no
    meh = none

The comment token can be overloaded with the ``comment_token`` argument.

    >>> conf.loads("""
    ...
    ... // this = comment
    ... # this = not a comment
    ...
    ... """, comment_token='//')
    {'# this': 'not a comment'}

Nested objects are optionally supported by setting the ``key_separator``
argument.

    >>> print conf.dumps({'a': 1, 'b': {'c': 3, 'd': 4}}, key_separator='::')
    a = 1
    b::c = 3
    b::d = 4

Here's a neat way to use nested objects to load your git config into Python.

    >>> import os
    >>> with os.popen('git config --list --local') as fp:
    ...     s = fp.read()
    ...     print s
    ...
    core.repositoryformatversion=0
    core.filemode=true
    core.bare=false
    core.logallrefupdates=true
    core.ignorecase=true
    core.precomposeunicode=true
    remote.origin.url=git@github.com:dwyer/simpleconf.git
    remote.origin.fetch=+refs/heads/*:refs/remotes/origin/*
    branch.master.remote=origin
    branch.master.merge=refs/heads/master
    >>> conf.loads(_, key_separator='.')
    {'core': {'logallrefupdates': True, 'precomposeunicode': True,
    'ignorecase': True, 'bare': False, 'filemode': True,
    'repositoryformatversion': 0}, 'remote': {'origin': {'url':
    'git@github.com:dwyer/simpleconf.git', 'fetch':
    '+refs/heads/*:refs/remotes/origin/*'}}, 'branch': {'master': {'merge':
    'refs/heads/master', 'remote': 'origin'}}}
