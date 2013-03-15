

def get_line_by_position(document, position):
    lines = enumerate(document.split('\n'), 1)

    pos = 0
    while pos < position:
        linenr, line = next(lines)
        pos += len(line)

    return linenr


def remember_line_number(obj, document, position):
    line = get_line_by_position(document, position)
    obj.__linenr__ = line


def get_line_number(obj):
    return getattr(obj, '__linenr__', None)
