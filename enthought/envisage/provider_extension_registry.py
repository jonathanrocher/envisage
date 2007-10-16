""" An extension registry implementation with multiple providers. """


# Standard library imports.
import logging

# Enthought library imports.
from enthought.traits.api import List, on_trait_change

# Local imports.
from extension_registry import ExtensionRegistry
from i_extension_provider import IExtensionProvider


# Logging.
logger = logging.getLogger(__name__)


class ProviderExtensionRegistry(ExtensionRegistry):
    """ An extension registry implementation with multiple providers. """

    ####  Private interface ###################################################

    # The extension providers that populate the registry.
    _providers = List(IExtensionProvider)

    ###########################################################################
    # 'object' interface.
    ###########################################################################

    def __init__(self, providers=None, **traits):
        """ Constructor. """

        super(ProviderExtensionRegistry, self).__init__(**traits)
        
        # This constructor exists because we want the caller to be able to
        # pass in a list of providers at creation time, but we don't that list
        # to be public, and we don't want the caller to be able to modify the
        # list dynamically.
        if providers is not None:
            map(self._add_provider, providers)
            
        return

    ###########################################################################
    # 'IExtensionRegistry' interface.
    ###########################################################################

    def set_extensions(self, extension_point_id, extensions):
        """ Set the extensions to an extension point.

        """

        raise SystemError('extension points cannot be set')
    
    ###########################################################################
    # Protected 'ExtensionRegistry' interface.
    ###########################################################################

    def _get_extensions(self, extension_point):
        """ Return the extensions for the given extension point. """

        # Has this extension point already been accessed?
        if extension_point in self._extensions:
            extensions = self._extensions[extension_point]

        # If not, then ask each provider for its contributions to the extension
        # point.
        else:
            extensions = self._initialize_extensions(extension_point)
            self._extensions[extension_point] = extensions

        # We store the extensions as a list of lists, with each inner list
        # containing the contributions from a single provider. Here we just
        # concatenate them into a single list.
        all = []
        for extensions in extensions:
            all.extend(extensions)
                
        return all

    ###########################################################################
    # 'ProviderExtensionRegistry' interface.
    ###########################################################################
        
    def add_provider(self, provider):
        """ Add an extension provider. """

        self._lk.acquire()
        events = self._add_provider(provider)
        self._lk.release()

        for extension_point_id, (refs, added, index) in events.items():
            self._call_listeners(refs, extension_point_id, added, [], index)

        return

    def remove_provider(self, provider):
        """ Remove an extension provider.

        Raise a 'ValueError' if the provider is not in the registry.

        """

        self._lk.acquire()
        events = self._remove_provider(provider)
        self._lk.release()

        for extension_point_id, (refs, removed, index) in events.items():
            self._call_listeners(refs, extension_point_id, [], removed, index)

        return
    
    ###########################################################################
    # Protected 'ProviderExtensionRegistry' interface.
    ###########################################################################

    def _add_provider(self, provider):
        """ Add a new provider. """

        # Each provider can contribute to multiple extension points, so we
        # build up a dictionary of the 'ExtensionPointChanged' events that we
        # need to fire.
        events = {}
        
        # Add the provider's extension points.
        self._add_provider_extension_points(provider)
        
        # Does the provider contribute any extensions to an extension point
        # that has already been accessed?
        for extension_point_id, extensions in self._extensions.items():
            new = provider.get_extensions(extension_point_id)
            if len(new) > 0:
                index = sum(map(len, extensions))
                refs  = self._get_listener_refs(extension_point_id)
                events[extension_point_id] = (refs, new[:], index)

            extensions.append(new)
            
        self._providers.append(provider)

        return events

    def _add_provider_extension_points(self, provider):
        """ Add a provider's extension points to the registry. """

        for extension_point in provider.get_extension_points():
            self._extension_points[extension_point.id] = extension_point

        return
    
    def _remove_provider(self, provider):
        """ Remove a provider. """

        # Each provider can contribute to multiple extension points, so we
        # build up a dictionary of the 'ExtensionPointChanged' events that we
        # need to fire.
        events = {}

        # Find the index of the provider in the provider list. Its
        # contributions are at the same index in the extensions list of lists.
        index = self._providers.index(provider)
        
        # Does the provider contribute any extensions to an extension point
        # that has already been accessed?
        for extension_point_id, extensions in self._extensions.items():
            old = extensions[index]
            if len(old) > 0:
                offset = sum(map(len, extensions[:index]))
                refs  = self._get_listener_refs(extension_point_id)
                events[extension_point_id] = (refs, old[:], offset)

            del extensions[index]

        self._providers.remove(provider)

        # Remove the provider's extension points.
        self._remove_provider_extension_points(provider, events)

        return events

    def _remove_provider_extension_points(self, provider, events):
        """ Remove a provider's extension points from the registry. """
        
        for extension_point in provider.get_extension_points():
            # Remove the extension point.
            del self._extension_points[extension_point.id]

            # Remove any extensions to the extension point.
            if extension_point.id in self._extensions:
                old = self._extensions[extension_point.id]
                del self._extensions[extension_point.id]

            else:
                old = []

            # Because the extension point was offered by the provider that we
            # are removing, the  chances are that nobody else is listening to
            # the extension point, but just to be sure.
            refs  = self._get_listener_refs(extension_point)
            events[extension_point] = (refs, old[:], 0)

        return

    ###########################################################################
    # Private interface.
    ###########################################################################

    #### Trait change handlers ################################################
    
    @on_trait_change('_providers.extension_point_changed')
    def _providers_extension_point_changed(self, obj, trait_name, old, event):
        """ Dynamic trait change handler. """

        if trait_name == 'extension_point_changed':
            logger.debug('provider <%s> extension point changed', obj)

            extension_point_id = event.extension_point_id
            
            self._lk.acquire()
            try:
                # This is a list of lists where each inner list contains the
                # contributions made to the extension point by a single
                # provider.
                extensions = self._extensions[extension_point_id]

                # Find the index of the provider in the provider list. Its
                # contributions are at the same index in the extensions list of
                # lists.
                provider_index = self._providers.index(obj)

                # Get the updated list from the provider.
                extensions[provider_index] = obj.get_extensions(
                    extension_point_id
                )

                # Find where the provider's contributions are in the whole
                # 'list'.
                offset = sum(map(len, extensions[:provider_index]))
                
                # Translate the event index from one that refers to the list of
                # contributions from the provider, to the list of contributions
                # from all providers.
                index = self._translate_index(event.index, offset)

                # Find out who is listening.
                refs = self._get_listener_refs(extension_point_id)

            finally:
                self._lk.release()

            # Let any listeners know that the extensions have been added.
            self._call_listeners(
                refs, extension_point_id, event.added, event.removed, index
            )

        return
        
    #### Methods ##############################################################
    
    def _initialize_extensions(self, extension_point_id):
        """ Initialize the extensions to an extension point. """

        extensions = []
        for provider in self._providers:
            extensions.append(provider.get_extensions(extension_point_id)[:])

        logger.debug('extensions to <%s>:<%s>', extension_point_id, extensions)

        return extensions

    def _translate_index(self, index, offset):
        """ Translate an event index by the given offset. """
        
        if isinstance(index, slice):
            index = slice(index.start+offset, index.stop+offset, index.step)

        else:
            index = index + offset

        return index
    
#### EOF ######################################################################
