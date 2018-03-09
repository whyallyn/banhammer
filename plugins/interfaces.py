"""Define interfaces to Targets."""
from ConfigParser import NoOptionError, NoSectionError, SafeConfigParser
from operator import itemgetter
import sys

from rest_framework import serializers

from plugins.exceptions import PluginError


class InterfaceMeta(type):
    """An interface metaclass."""
    # we use __init__ rather than __new__ here because we want modify
    # attributes of the class *after* they have been created
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, 'registry'):
            # this is the base class. Create a dictionary of registered classes
            cls.registry = {}
        else:
            # this is a derived class. Add cls to the dictionary
            interface_id = name.lower()
            cls.registry[interface_id] = cls
        super(InterfaceMeta, cls).__init__(name, bases, dct)


class TargetInterfaceMeta(InterfaceMeta):
    """An interface metaclass for Targets."""
    pass


class Ip(object):
    """A class for registering IP plugins."""
    __metaclass__ = TargetInterfaceMeta


class Domain(object):
    """A class for registering Domain plugins."""
    __metaclass__ = TargetInterfaceMeta


class Url(object):
    """A class for registering URL plugins."""
    __metaclass__ = TargetInterfaceMeta


class Hash(object):
    """A class for registering Hash plugins."""
    __metaclass__ = TargetInterfaceMeta


class User(object):
    """A class for registering User plugins."""
    __metaclass__ = TargetInterfaceMeta


def get_docstring(function):
    """Get the docstring of a function."""
    docstring = function.__doc__
    # let user know their method is missing a docstring
    if not docstring:
        docstring = 'Method is missing docstring.'
    # cleanup docstring of unnecessary whitespace
    else:
        docstring = ' '.join(docstring.split())
    return docstring


def get_method_weight(method):
    """Get the configured method weight, otherwise set to 0."""
    config = SafeConfigParser()
    config.read('plugins.ini')
    try:
        # grab configuration options for method weights
        weight = config.getint('plugin_method_weights', method)
    except (NoOptionError, NoSectionError):
        weight = 0
    return weight


class TargetInterface(object):
    """A class for getting and running plugin methods for a target."""
    def __init__(self, target, target_type, reason=None):
        self.target = target
        self.reason = reason
        # import plugins before creating interface to registry of classes
        __import__('plugins.%s_plugins' % target_type)
        # get the correct class by target_type name
        self.registry = getattr(
            sys.modules[__name__], target_type.title()).registry

    def run_method(self, method):
        """Run a method on a Target."""
        plugin_class = method.split('_')[0]
        plugin_method = method.split('_', 1)[1]

        try:
            target = self.registry[plugin_class](
                self.target,
                self.reason
            )
            method = getattr(target, plugin_method)
            method()
        # catch errors from plugin
        except PluginError as err:
            raise serializers.ValidationError(
                {err.plugin: [err.message]})
        except KeyError:
            raise serializers.ValidationError(
                {'plugin': ['Invalid plugin method.']})
        except:
            raise serializers.ValidationError(
                {'plugin': ['Unhandled exception in plugin method.']})

    @property
    def plugins(self):
        """Get a dictionary of plugins and methods for this Target."""
        plugins = {}
        for key, obj in self.registry.iteritems():
            for mtd in dir(obj):
                if callable(getattr(obj, mtd)) and not mtd.startswith('_'):
                    if key not in plugins:
                        plugins[key] = []
                    plugins[key].append({
                        'method': '%s_%s' % (key, mtd),
                        'description': get_docstring(getattr(obj, mtd)),
                        'weight': get_method_weight('%s_%s' % (key, mtd)),
                    })
        return plugins

    @property
    def methods(self):
        """Get a sorted (by weight) list of methods for this Target."""
        methods = []
        for dict_values in self.plugins.itervalues():
            for value in dict_values:
                methods.append(value)
        methods_sorted_by_weight = sorted(
            methods, key=itemgetter('weight'), reverse=True)
        return [val['method'] for val in methods_sorted_by_weight]
