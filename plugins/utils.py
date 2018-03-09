"""Miscellaneous utility functions shared by BanHammer plugins."""
from ConfigParser import NoSectionError, SafeConfigParser
import contextlib
import random
import string

from plugins.exceptions import PluginError


def generate_random_string(length):
    """Generate a random string."""
    return ''.join(random.SystemRandom().choice(
        string.letters + string.digits + string.punctuation) for _ in range(
            length))


def get_plugin_config_options(section):
    """Get configuration options from plugins.ini."""
    config = SafeConfigParser()
    config.read('plugins.ini')
    try:
        return dict(config.items(section))
    except NoSectionError:
        raise PluginError('No "%s" section in plugins.ini' % section)


def convert_str_tolist(astring):
    """Convert a string into a list, splitting each value by comma."""
    return map(str.strip, astring.strip(',').split(','))


@contextlib.contextmanager
def capture_stdout():
    """Capture stdout from Python script."""
    import sys
    from cStringIO import StringIO
    oldout, olderr = sys.stdout, sys.stderr
    try:
        stdout = [StringIO(), StringIO()]
        sys.stdout, sys.stderr = stdout
        yield stdout
    finally:
        sys.stdout, sys.stderr = oldout, olderr
        stdout[0] = stdout[0].getvalue()
        stdout[1] = stdout[1].getvalue()
