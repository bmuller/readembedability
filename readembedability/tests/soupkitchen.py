import html


class Tag(object):
    def __init__(self, name):
        self.name = name
        self.kids = []
        self.attrs = {}

    def __call__(self, *kids, **attrs):
        kids = list(kids)
        self.attrs = attrs
        if kids and isinstance(kids[-1], dict):
            self.attrs.update(kids.pop())

        for kid in kids:
            if isinstance(kid, Tag):
                self.kids.append(kid)
            else:
                cleaned = html.escape(str(kid))
                self.kids.append(cleaned)

        return self

    def __str__(self):
        # pylint: disable=not-an-iterable
        sattrs = " ".join(["%s=\"%s\"" % kv for kv in self.attrs.items()])
        sattrs = " " + sattrs if self.attrs else ""
        if not self.kids:
            return "<%s%s/>" % (self.name, sattrs)
        result = "<%s%s>" % (self.name, sattrs)
        result += "".join(map(str, self.kids))
        return result + "</%s>" % self.name

    __repr__ = __str__


class TagGenerator(object):
    def __getattr__(self, name):
        return Tag(name)

T = TagGenerator()
