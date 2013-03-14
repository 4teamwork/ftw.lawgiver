from zope.configuration.interfaces import InvalidToken
from zope.interface import implements
from zope.schema import List
from zope.schema import TextLine
from zope.schema import ValidationError
from zope.schema.interfaces import IFromUnicode


class CommaSeparatedText(List):
    implements(IFromUnicode)

    def __init__(self, *args, **kwargs):
        if 'value_type' not in kwargs:
            kwargs['value_type'] = TextLine()
        super(CommaSeparatedText, self).__init__(*args, **kwargs)

    def fromUnicode(self, u):
        u = u.strip()
        if u:
            vt = self.value_type.bind(self.context)
            values = []
            for s in u.split(','):
                try:
                    v = vt.fromUnicode(s).strip()
                except ValidationError, v:
                    raise InvalidToken("%s in %s" % (v, u))
                else:
                    values.append(v)
        else:
            values = []

        self.validate(values)

        return values
