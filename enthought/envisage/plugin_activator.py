""" The default plugin activator. """


# Enthought library imports.
from enthought.traits.api import HasTraits, implements

# Local imports.
from i_plugin_activator import IPluginActivator


class PluginActivator(HasTraits):
    """ The default plugin activator. """

    implements(IPluginActivator)
    
    ###########################################################################
    # 'IPluginActivator' interface.
    ###########################################################################

    def start_plugin(self, plugin):
        """ Start the specified plugin. """

        # Connect all of the plugin's extension point traits so that the plugin
        # will be notified if and when contributions are added or removed.
        plugin.connect_extension_point_traits()

        # Register all service traits.
        plugin.register_services()

        # Plugin specific start.
        plugin.start()
        
        return

    def stop_plugin(self, plugin):
        """ Stop the specified plugin. """

        # Plugin specific stop.
        plugin.stop()

        # Unregister all service traits.
        plugin.unregister_services()

        return

#### EOF ######################################################################
