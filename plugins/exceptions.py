"""Define plugin exceptions."""
import inspect
import os


class PluginError(Exception):
    """An exception class for plugins."""
    def __init__(self, message, plugin=None):
        # call the base class constructor with the parameters it needs
        super(PluginError, self).__init__(message)
        # add the plugin name to the error message if not manually passed
        self.plugin = plugin
        if not plugin:
            frame = inspect.stack()[1]
            filename = inspect.getmodule(
                frame[0]).__file__
            self.plugin = os.path.splitext(os.path.basename(filename))[0]
