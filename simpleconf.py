_DEFAULT_ASSIGNMENT_OPERATOR = '='
_DEFAULT_COMMENT_TOKEN = '#'
_DEFAULT_ESCAPE_TOKEN = '\\'
_DEFAULT_KEYWORDS = {'true': True, 'false': False, 'null': None}


class ConfConf(object):

    def __init__(self, assignment_operator=None, comment_token=None,
                 escape_token=None, keywords=None, key_separator=None,
                 key_validator=None):
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

    def __init__(self, parse_int=None, parse_float=None, strict=False,
                 object_type=None, assignment_operator=None,
                 comment_token=None, escape_token=None, keywords=None,
                 key_separator=None, key_validator=None):
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

    def __init__(self, sort_keys=False, assignment_operator=None,
                 comment_token=None, escape_token=None, keywords=None,
                 key_separator=None, key_validator=None):
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
