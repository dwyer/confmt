import io


class ConfDecoder:

    def __init__(self, encoding='utf-8', object_hook=dict,
                 parse_int=int, parse_float=float, **kwargs):
        self.encoding = encoding
        self.object_hook = object_hook
        self.parse_int = parse_int
        self.parse_float = parse_float
        # experimental:
        self.true_token = kwargs.get('true_token', 'true')
        self.false_token = kwargs.get('false_token', 'false')
        self.none_token = kwargs.get('none_token', 'null')
        self.comment_token = kwargs.get('comment_token', '#')
        self.assignment_operator = kwargs.get('assignment_operator', '=')
        self.strict_mode = kwargs.get('strict_mode', False)
        self.variable_validator = kwargs.get('variable_validator',
                                             lambda _: True)

    def load(self, fp):
        env = self.object_hook()
        for i, line in enumerate(fp):
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

    def loads(self, s):
        return self.load(io.StringIO(unicode(s.decode(self.encoding))))


def _isa(s, t):
    try:
        t(s)
        return True
    except ValueError:
        return False


def load(fp, **kwargs):
    return ConfDecoder(**kwargs).load(fp)


def loads(s, **kwargs):
    return ConfDecoder(**kwargs).loads(s)
