import cgi


class Tag(object):
    def __init__(self, name):
        self.name = name
        self.kids = []
        self.attrs = {}

    def __call__(self, *kids, **attrs):
        self.kids = list(kids)
        self.attrs = attrs
        if len(self.kids) > 0 and type(self.kids[-1]) is dict:
            self.attrs.update(self.kids.pop())
        self.kids = map(lambda s: s if type(s) is Tag else cgi.escape(str(s)), self.kids)
        return self

    def __str__(self):
        sattrs = " ".join(["%s=\"%s\"" % kv for kv in self.attrs.items()])
        sattrs = " " + sattrs if len(self.attrs) > 0 else ""
        if len(self.kids) == 0:
            return "<%s%s/>" % (self.name, sattrs)
        return "<%s%s>" % (self.name, sattrs) + "".join(map(str, self.kids)) + "</%s>" % self.name

    __repr__ = __str__


class TagGenerator(object):
    def __getattr__(self, name):
        return Tag(name)

T = TagGenerator()
