from collections import defaultdict
from datetime import datetime


class ParseResult:
    def __init__(self, url):
        self.props = {}

        # this is used for logging
        self.current_parser = None
        self.log = defaultdict(list)

        self.set('url', str(url), 4)
        self.set('embed', False)
        self.set('primary_image', None)
        self.set('secondary_images', [])
        self.set('content', None)
        self.set('summary', None)
        self.set('title', None)
        self.set('subtitle', None)
        self.set('authors', [])
        self.set('published_at', None)
        self.set('keywords', [])
        self.set('canonical_url', None)
        self.set('success', False)

    def set_parser_name(self, name):
        self.current_parser = name

    def set_if(self, prop, value, **kwargs):
        """
        Just like set, but only set 'if value'.  Lazy!
        """
        if value:
            return self.set(prop, value, **kwargs)

    def set(self, prop, value, confidence=0, tiebreaker=None):
        """
        Set the prop if confidence is higher than what's already set,
        if not value is already set, or if same confidence as what's
        already set if the value is better according to tiebreaker
        (which is a method of the Evaluator class)

        Confidences:
          0 A guess
          1 Fairly sure
          2 Mostly sure
          3 Sure
          4 Max.  Bet your life.
        """
        confidence = min(confidence, 4)

        # log this for later debugging
        if self.current_parser:
            self.log[prop].append((self.current_parser, value, confidence))

        if prop in self.props:
            if confidence < self.props[prop][1]:
                return self
            if confidence == self.props[prop][1] and tiebreaker:
                value = Evaluator.best(self.get(prop), value, tiebreaker)
        self.props[prop] = (value, confidence)
        return self

    def has(self, prop):
        value = self.get(prop)
        return value is not None and len(value) > 0

    def add(self, prop, items, confidence=None, unique=True):
        """
        If confidence is None, then the current value will be used if items
        already exist (and the default for the set method if not)
        """
        if prop not in self:
            values = list(set(items)) if unique else items
            if confidence is None:
                return self.set(prop, values)
            return self.set(prop, values, confidence)

        value, exconf = self.props[prop]
        value += items
        value = list(set(value)) if unique else value
        nconf = exconf if confidence is None else confidence
        return self.set(prop, value, nconf)

    def get(self, prop, default=None):
        if prop in self:
            return self.props[prop][0]
        return default

    def to_dict(self):
        # pylint: disable=not-an-iterable,consider-iterating-dictionary
        keys = [k for k in self.props.keys() if not k.startswith('_')]
        return {k: self.get(k) for k in keys}

    def __str__(self):
        """
        For debugging.
        """
        # pylint: disable=not-an-iterable
        parts = []
        for k, vconf in self.props.items():
            value, confidence = vconf
            parts += ["(%i) %s = %s" % (confidence, k, value)]
        return "\n\n".join(parts)

    def __contains__(self, prop):
        return prop in self.props


class Evaluator:
    """
    A class to contain logic to compare two values.  Used in cases
    where two parsers have the same confidence in a value to break
    a tie.
    """
    @classmethod
    def best(cls, first, second, method):
        if not hasattr(cls, method):
            raise RuntimeError("No evaluator method %s" % method)
        func = getattr(cls, method)
        return first if func(first) > func(second) else second

    @classmethod
    def textquality(cls, value):
        verbotten = ['email preference', 'privacy policy']
        score = 0
        value = value.lower()
        for verb in verbotten:
            if verb in value:
                score -= 1
        return score

    @classmethod
    def textlength(cls, value):
        return len(value) if value else 0

    @classmethod
    def timespecificity(cls, dttm):
        if not isinstance(dttm, datetime):
            return 0
        # more non-zeros to the right = more better
        return len(str(dttm).rstrip('0: '))
