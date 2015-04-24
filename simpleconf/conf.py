class ConfBase(object):

    def __init__(self, **kwargs):
        # experimental:
        self.true_token = kwargs.get('true_token', 'true')
        self.false_token = kwargs.get('false_token', 'false')
        self.none_token = kwargs.get('none_token', 'null')
        self.comment_token = kwargs.get('comment_token', '#')
        self.assignment_operator = kwargs.get('assignment_operator', '=')
        self.variable_validator = kwargs.get('variable_validator',
                                             lambda _: True)


class ConfDecoder(ConfBase):

    def __init__(self, object_hook=dict, parse_int=int, parse_float=float,
                 parse_constant=None, strict_mode=False, **kwargs):
        self.object_hook = object_hook
        self.parse_int = parse_int
        self.parse_float = parse_float
        self.parse_constant = parse_constant
        self.strict_mode = strict_mode
        super(ConfDecoder, self).__init__(**kwargs)

    def decode(self, s):
        env = self.object_hook()
        for i, line in enumerate(s.splitlines()):
            s = line.strip()
            if not s or s.startswith(self.comment_token):
                continue
            try:
                var, val = s.split(self.assignment_operator, 1)
            except ValueError:
                if self.strict_mode:
                    raise ValueError(
                        'missing assignment operator %s on line %d: %s' % (
                            repr(self.assignment_operator), i + 1, repr(line)))
                continue
            var = var.strip()
            if not self.variable_validator(var):
                if self.strict_mode:
                    raise ValueError('invalid variable name: %s' % repr(var))
                continue
            val = val.strip()
            if val == self.true_token:
                val = True
            elif val == self.false_token:
                val = False
            elif val == self.none_token:
                val = None
            elif _isa(val, int):
                val = self.parse_int(val)
            elif _isa(val, float):
                val = self.parse_float(val)
            env[var] = val
        return env


class ConfEncoder(ConfBase):

    def __init__(self, sort_keys=False, spacing=True, **kwargs):
        self.sort_keys = sort_keys
        self.spacing = spacing
        super(ConfEncoder, self).__init__(**kwargs)

    def encode(self, env):
        lines = []
        items = env.items()
        if self.sort_keys:
            items.sort()
        separator = self.assignment_operator
        if self.spacing:
            separator = ' %s ' % separator
        for var, val in items:
            assert isinstance(var, basestring)
            if not self.variable_validator(var):
                raise ValueError('invalid variable name: %s' % repr(var))
            if val is True:
                val = self.true_token
            elif val is False:
                val = self.false_token
            elif val is None:
                val = self.none_token
            elif isinstance(val, int) or isinstance(val, float):
                val = str(val)
            else:
                assert isinstance(val, basestring), "can't serialize: %s" % val
            lines.append(separator.join((var, val)).strip())
        return '\n'.join(lines)


def _isa(s, t):
    try:
        t(s)
        return True
    except ValueError:
        return False


def dump(env, fp, **kwargs):
    fp.write(dumps(env, **kwargs))


def dumps(env, **kwargs):
    return ConfEncoder(**kwargs).encode(env)


def load(fp, **kwargs):
    return loads(fp.read(), **kwargs)


def loads(s, **kwargs):
    return ConfDecoder(**kwargs).decode(s)
