import datetime


def timestamp():
    """Return a timestamp in "YYYY-MM-DD hh:mm:ss" format."""
    dt = datetime.datetime.now()
    return "%04d-%02d-%02d %02d:%02d:%02d" % (dt.year, dt.month, dt.day,
                                              dt.hour, dt.minute, dt.second)


class ANSI(object):
    """ANSI control sequences."""
    BOLD = '\u001b[1m'
    END = '\u001b[0m'
    BLUE = '\u001b[34m'
    RED = '\u001b[31m'
