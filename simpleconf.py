"""simpleconf is a very simple and easy data-interchange format for
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

    >>> import simpleconf
    >>> simpleconf.loads('''
    ...
    ... # this is a comment
    ...
    ... # the following is a statement
    ... energy = mass times the speed of light squared
    ...
    ... ''')
    {'energy': 'mass times the speed of light squared'}

Only the first assignment operator is evaluated.

    >>> simpleconf.loads('relativity = e = mc^2')
    {'relativity': 'e = mc^2'}

Numbers, booleans and "null" evaluate to their primitive counterparts.

    >>> simpleconf.loads('''
    ...
    ... answer = 42
    ... phish = 1.618
    ... yes = true
    ... no = false
    ... maybe = null
    ...
    ... ''')
    {'answer': 42, 'maybe': None, 'yes': True, 'phish': 1.618, 'no': False}

Key names evaluate to strings and can contain any character except the
assignment operator.

    >>> simpleconf.loads('''
    ...
    ... two birds = 2
    ... one stone = 1
    ... three's a "crowd"? = true
    ...
    ... ''')
    {'one stone': 1, 'two birds': 2, 'three\'s a "crowd"?': True}

The deserialized object is a ``dict`` by default, but can be configured with
the ``object_type`` argument. For example, you could use an OrderedDict to
preserve the order.

    >>> import collections
    >>> simpleconf.loads('''
    ...
    ... one = 1
    ... two = 2
    ... tree = 3
    ...
    ... ''', object_type=collections.OrderedDict)
    OrderedDict([(u'one', 1), (u'two', 2), (u'tree', 3)])

Numbers are deserialized to ``int`` and ``float`` by default, but can be
configured with the ``parse_int`` and ``parse_float`` arguments.

    >>> import decimal
    >>> simpleconf.loads('''
    ...
    ... answer = 42
    ... phish = 1.618
    ...
    ... ''', parse_int=float, parse_float=decimal.Decimal)
    {'answer': 42.0, 'phish': Decimal('1.618')}

Syntax Configuration
====================

Note: the following examples apply to all classes and functions.

The assignment operator can be overloaded with the ``assignment_operator``
argument.

    >>> simpleconf.loads('''
    ...
    ... a: 1
    ... b: 52
    ... this = key: value
    ...
    ... ''', assignment_operator=':')
    {'a': 1, 'this = key': 'value', 'b': 52}

    >>> print simpleconf.dumps(_, assignment_operator=':')
    a : 1
    this = key : value
    b : 52

The keywords corresponding to ``True``, ``False`` and ``None`` can be
overloaded with the ``keywords`` argument to ``load`` and ``loads``.

    >>> keywords = {'yes': True, 'no': False, 'none': None}
    >>> simpleconf.loads('''
    ...
    ... yep = yes
    ... nah = no
    ... meh = none
    ...
    ... ''', keywords=keywords)
    {'yep': True, 'nah': False, 'meh': None}
    >>> print simpleconf.dumps(_, keywords=keywords)
    yep = yes
    nah = no
    meh = none

The comment token can be overloaded with the ``comment_token`` argument.

    >>> simpleconf.loads('''
    ...
    ... // this = comment
    ... # this = not a comment
    ...
    ... ''', comment_token='//')
    {'# this': 'not a comment'}

Nested objects are optionally supported by setting the ``key_separator``
argument.

    >>> print simpleconf.dumps({'a': 1, 'b': {'c': 3, 'd': 4}},
                               key_separator='::')
    a = 1
    b::c = 3
    b::d = 4

Here's a neat way to use nested objects to load your git config into Python.

    >>> import os
    >>> with os.popen('git config --list --local') as fp:
    ...     s = fp.read()
    ...
    >>> print s
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

    >>> simpleconf.loads(_, key_separator='.')
    {'core': {'logallrefupdates': True, 'precomposeunicode': True,
    'ignorecase': True, 'bare': False, 'filemode': True,
    'repositoryformatversion': 0}, 'remote': {'origin': {'url':
    'git@github.com:dwyer/simpleconf.git', 'fetch':
    '+refs/heads/*:refs/remotes/origin/*'}}, 'branch': {'master': {'merge':
    'refs/heads/master', 'remote': 'origin'}}}
"""

__all__ = ['ConfDecoder', 'ConfEncoder', 'dump', 'dumps', 'load', 'loads']
__author__ = 'Casey Dwyer <caseydwyer@gmail.com>'
__version__ = '0.0.0'

try:
    basestring
except NameError:
    basestring = str

_DEFAULT_ASSIGNMENT_OPERATOR = '='
_DEFAULT_COMMENT_TOKEN = '#'
_DEFAULT_ESCAPE_TOKEN = '\\'
_DEFAULT_KEYWORDS = {'true': True, 'false': False, 'null': None}


class ConfConf(object):
    """Base-class for ``ConfDecoder`` and ``ConfEncoder``.
    """

    def __init__(self, assignment_operator=None, comment_token=None,
                 escape_token=None, keywords=None, key_separator=None,
                 key_validator=None):
        """``assignment_operator`` is a ``str`` used to split and/or join
        key/value pairs. The default value is '='.

        ``comment_token`` is a ``str`` used to indicate the beginning of a
        comment. Lines starting with this value will be ignored by the decoder.
        Key names containing this value will raise a ``ValueError`` in the
        encoder. The default value is '#'.

        ``keywords`` is a ``dict`` mapping a series of keywords to their
        corresponding constant primitive values. Each keyword must be a ``str``
        and each value should be a singleton, as keyword values will be looked
        up by the encoder using the ``is`` operator. The default value is
        {'true': True, 'false': False, 'null': None}.

        ``key_separator``, is a ``str`` used to indicate nested of
        objects/environments. If set, the decoder will use it nest objects, and
        the encoder will use it to serialize nested objects into a linear
        sequence of statements. The default value is ``None``.

        ``key_validator`` is a function that accepts one argument, a key name
        ``str``, and returns a non-true value if the key name is invalid. If
        this validation fails in the encoder, or in the decoder with strict
        mode enabled, a ``ValueError`` will be raised. If it fails in the
        decoder with strict mode disabled, the statment containing the invalid
        key name will be ignored. The default value is ``None``.

        """
        self.assignment_operator = (
            _DEFAULT_ASSIGNMENT_OPERATOR if assignment_operator is None else
            assignment_operator)
        self.comment_token = (
            _DEFAULT_COMMENT_TOKEN if comment_token is None else comment_token)
        self.escape_token = (
            _DEFAULT_ESCAPE_TOKEN if escape_token is None else escape_token)
        self.keywords = _DEFAULT_KEYWORDS if keywords is None else keywords
        self.key_separator = key_separator
        self.key_validator = key_validator


class ConfDecoder(ConfConf):
    """The format decoder.

    """

    def __init__(self, parse_int=None, parse_float=None, strict=False,
                 object_type=None, assignment_operator=None,
                 comment_token=None, escape_token=None, keywords=None,
                 key_separator=None, key_validator=None):
        """``parse_int`` is a function that accepts one argument, the ``str``
        representation of an integer to be decoded, and returns a parsed
        value. The default value is ``int``.

        ``parse_float`` is a function that accepts one argument, the ``str``
        representation of a real number to be decoded, and returns a parsed
        value. The default value is ``float``.

        ``strict``, if true, will cause the decoder to raise a ``ValueError``
        when an invalid statment is encounted. The default value is ``False``.

        ``object_type``, is a class or function that takes no arguments and
        returns the initial value of the object/environment to be returned.
        The default value is ``dict``.

        See ``ConfConf`` for definitions of other parameters.

        """
        super(ConfDecoder, self).__init__(
            assignment_operator=assignment_operator,
            comment_token=comment_token,
            keywords=keywords, key_separator=key_separator,
            key_validator=key_validator, escape_token=escape_token)
        self.parse_int = parse_int or int
        self.parse_float = parse_float or float
        self.strict = strict
        self.object_type = object_type or dict

    def __split(self, s, sep, maxsplit=-1):
        if not self.escape_token:
            return s.split(sep, maxsplit)
        if maxsplit == 0:
            return [s]
        esep = self.escape_token + sep
        toks = []
        chrs = []
        i = 0
        while i < len(s):
            if s[i:i+len(sep)] == sep:
                toks.append(''.join(chrs))
                i += len(sep)
                if maxsplit > -1:
                    maxsplit -= 1
                    if not maxsplit:
                        chrs = s[i:]
                        break
                chrs = []
            elif s[i:i+len(esep)] == esep:
                chrs.append(sep)
                i += len(esep)
            else:
                chrs.append(s[i])
                i += 1
        toks.append(''.join(chrs))
        return toks

    def __validate_keys(self, *args):
        if self.key_validator:
            for key in args:
                if not self.key_validator(key):
                    if self.strict:
                        raise ValueError('invalid key: %s' % repr(key))
                    return False
        return True

    def decode(self, s):
        obj = self.object_type()
        for i, line in enumerate(s.splitlines()):
            s = line.strip()
            if not s:
                continue
            if self.comment_token:
                if self.escape_token:
                    s = self.__split(s, self.comment_token, 1)[0].strip()
                    if not s:
                        continue
                elif s.startswith(self.comment_token):
                    continue
            try:
                key, val = self.__split(s, self.assignment_operator, 1)
            except ValueError:
                if self.strict:
                    raise ValueError(
                        'missing assignment operator %s on line %d: %s' % (
                            repr(self.assignment_operator), i + 1, repr(line)))
                continue
            val = val.strip()
            if val in self.keywords:
                val = self.keywords[val]
            elif _isa(val, int):
                val = self.parse_int(val)
            elif _isa(val, float):
                val = self.parse_float(val)
            if self.key_separator:
                keys = self.__split(key, self.key_separator)
                keys = [key.strip() for key in keys]
                if not self.__validate_keys(*keys):
                    continue
                base_obj = obj
                for j, key in enumerate(keys):
                    if j == len(keys) - 1:
                        obj[key] = val
                        break
                    if key not in obj or not hasattr(obj[key], '__setitem__'):
                        obj[key] = self.object_type()
                    obj = obj[key]
                obj = base_obj
            else:
                key = key.strip()
                if not self.__validate_keys(key):
                    continue
                obj[key] = val
        return obj


class ConfEncoder(ConfConf):
    """The format encoder.

    """

    def __init__(self, sort_keys=False, assignment_operator=None,
                 comment_token=None, escape_token=None, keywords=None,
                 key_separator=None, key_validator=None):
        """``sort_keys``, if true, will encode all key/value pairs in sorted
        order. The default value is false.

        See ``ConfConf`` for definitions of other parameters.

        """
        super(ConfEncoder, self).__init__(
            assignment_operator=assignment_operator,
            comment_token=comment_token,
            keywords=keywords, key_separator=key_separator,
            key_validator=key_validator, escape_token=escape_token)
        self.sort_keys = sort_keys
        self.separator = ' %s ' % self.assignment_operator

    def __encode(self, obj, base_key=None):
        val = None
        for keyword, constant in self.keywords.items():
            if obj is constant:
                val = keyword
                break
        if val is None:
            if isinstance(obj, int) or isinstance(obj, float):
                val = str(obj)
            elif isinstance(obj, basestring):
                val = obj
        if val is not None:
            val = val.strip()
            val = self.__escape(val, self.comment_token)
            if base_key is not None:
                return self.separator.join((base_key, val))
            return val
        if base_key is not None and not self.key_separator:
            # We're more than one level deep and this configuration doesn't
            # support nesting, so let's bail.
            raise TypeError('value is not serializable: %s' % repr(obj))
        lines = []
        if hasattr(obj, 'items'):
            pairs = obj.items()
        elif hasattr(obj, '__iter__'):
            # Let's assume that this is an iterable of key/value pairs.
            # TODO: Confirm it.
            pairs = obj
        else:
            raise TypeError('value is not serializable: %s' % repr(obj))
        if self.sort_keys:
            pairs.sort()
        for key, val in pairs:
            if not isinstance(key, basestring):
                raise TypeError('key must be a string: %s' % repr(key))
            key = key.strip()
            key = self.__escape(key, self.assignment_operator,
                                self.comment_token, self.key_separator)
            if self.key_validator and not self.key_validator(key):
                raise ValueError('invalid key: %s' % repr(key))
            if self.key_separator and base_key is not None:
                key = self.key_separator.join((base_key, key))
            lines.append(self.__encode(val, base_key=key))
        return '\n'.join(lines)

    def __escape(self, s, *args):
        if not self.escape_token:
            return s
        for tok in args:
            if tok is not None:
                s = s.replace(tok, '\\' + tok)
        return s

    def encode(self, obj):
        return self.__encode(obj)


def _isa(s, t):
    try:
        t(s)
        return True
    except ValueError:
        return False


def dump(obj, fp, sort_keys=False, assignment_operator=None,
         comment_token=None, escape_token=None, keywords=None,
         key_separator=None, key_validator=None):
    fp.write(dumps(
        obj, sort_keys=sort_keys, assignment_operator=assignment_operator,
        comment_token=comment_token, escape_token=escape_token,
        keywords=keywords, key_separator=key_separator,
        key_validator=key_validator))


def dumps(obj, sort_keys=False, assignment_operator=None, comment_token=None,
          escape_token=None, keywords=None, key_separator=None,
          key_validator=None):
    encoder = ConfEncoder(
        sort_keys=sort_keys, assignment_operator=assignment_operator,
        comment_token=comment_token, escape_token=escape_token,
        keywords=keywords, key_separator=key_separator,
        key_validator=key_validator)
    return encoder.encode(obj)


def load(fp, parse_int=None, parse_float=None, strict=False, object_type=None,
         assignment_operator=None, comment_token=None, escape_token=None,
         keywords=None, key_separator=None, key_validator=None):
    return loads(
        fp.read(), parse_int=parse_int, parse_float=parse_float, strict=strict,
        object_type=object_type, assignment_operator=assignment_operator,
        comment_token=comment_token, escape_token=escape_token,
        keywords=keywords, key_separator=key_separator,
        key_validator=key_validator)


def loads(s, parse_int=None, parse_float=None, strict=False, object_type=None,
          assignment_operator=None, comment_token=None, escape_token=None,
          keywords=None, key_separator=None, key_validator=None):
    decoder = ConfDecoder(
        parse_int=parse_int, parse_float=parse_float, strict=strict,
        object_type=object_type, assignment_operator=assignment_operator,
        comment_token=comment_token, escape_token=escape_token,
        keywords=keywords, key_separator=key_separator,
        key_validator=key_validator)
    return decoder.decode(s)
