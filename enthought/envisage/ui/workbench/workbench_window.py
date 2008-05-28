""" An extensible workbench window. """


# Standard library imports.
import logging

# Enthought library imports.
import enthought.pyface.workbench.api as pyface

from enthought.envisage.api import IExtensionPointUser, IExtensionRegistry
from enthought.envisage.api import IServiceRegistry
from enthought.envisage.api import ExtensionPoint, ServiceRegistry
from enthought.envisage.ui.action.api import ActionSet
from enthought.pyface.action.api import StatusBarManager
from enthought.pyface.workbench.api import IPerspective
from enthought.traits.api import Delegate, Instance, List, Property, implements

# Local imports.
from workbench_action_manager_builder import WorkbenchActionManagerBuilder
from workbench_editor_manager import WorkbenchEditorManager


# Logging.
logger = logging.getLogger(__name__)


class WorkbenchWindow(pyface.WorkbenchWindow):
    """ An extensible workbench window. """

    implements(IServiceRegistry, IExtensionPointUser)
    
    # Extension point Ids.
    ACTION_SETS    = 'enthought.envisage.ui.workbench.action_sets'
    VIEWS          = 'enthought.envisage.ui.workbench.views'
    PERSPECTIVES   = 'enthought.envisage.ui.workbench.perspectives'
    SERVICE_OFFERS = 'enthought.envisage.ui.workbench.service_offers'

    # DEPRECATED extension point Ids.
    ACTIONS      = 'enthought.envisage.ui.workbench.actions'
    
    #### 'WorkbenchWindow' interface ##########################################

    # The application that the view is part of.
    #
    # This is equivalent to 'self.workbench.application', and is provided just
    # as a convenience since windows often want access to the application.
    application = Delegate('workbench', modify=True)

    # The action sets that provide the toolbars, menus groups and actions
    # used in the window.
    action_sets = List(Instance(ActionSet))

    # The service registry for 'per window' services.
    service_registry = Instance(IServiceRegistry, factory=ServiceRegistry)

    #### 'IExtensionPointUser' interface ######################################

    # The extension registry that the object's extension points are stored in.
    extension_registry = Property(Instance(IExtensionRegistry))

    #### Private interface ####################################################

    # The workbench menu and tool bar builder.
    #
    # The builder is used to create the window's tool bar and menu bar by
    # combining all of the contributed action sets.
    _action_manager_builder = Instance(WorkbenchActionManagerBuilder)
    
    # Contributed action sets.
    _action_sets = ExtensionPoint(id=ACTION_SETS)

    # Contributed views (views are contributed as factories not view instances
    # as each workbench window requires its own).
    _views = ExtensionPoint(id=VIEWS)

    # Contributed perspectives.
    _perspectives = ExtensionPoint(id=PERSPECTIVES)

    # Contributed service offers.
    _service_offers = ExtensionPoint(id=SERVICE_OFFERS)

    # The Ids of the services that were automatically registered.
    _service_ids = List
    
    # DEPRECATED: Contributed action sets.
    _actions = ExtensionPoint(id=ACTIONS)
    
    ###########################################################################
    # 'IExtensionPointUser' interface.
    ###########################################################################

    def _get_extension_registry(self):
        """ Trait property getter. """

        return self.application

    ###########################################################################
    # 'pyface.Window' interface.
    ###########################################################################

    #### Trait initializers ###################################################
    
    def _menu_bar_manager_default(self):
        """ Trait initializer. """
        
        return self._action_manager_builder.create_menu_bar_manager('MenuBar')

    def _status_bar_manager_default(self):
        """ Trait initializer. """

        return StatusBarManager()
    
    def _tool_bar_managers_default(self):
        """ Trait initializer. """

        return self._action_manager_builder.create_tool_bar_managers('ToolBar')

    #### Trait change handlers ################################################

    def _opening_changed(self):
        """ Static trait change handler. """

        self._service_ids = self._register_service_offers(self._service_offers)

        return

    def _closed_changed(self):
        """ Static trait change handler. """

        self._unregister_service_offers(self._service_ids)

        return
        
    ###########################################################################
    # 'pyface.WorkbenchWindow' interface.
    ###########################################################################

    #### Trait initializers ###################################################

    def _editor_manager_default(self):
        """ Trait initializer. """

        return WorkbenchEditorManager(window=self)
    
    def _icon_default(self):
        """ Trait initializer. """

        return self.workbench.application.icon
    
    def _perspectives_default(self):
        """ Trait initializer. """

        perspectives = []
        for factory_or_perspective in self._perspectives:
            # Is the contribution an actual perspective, or is it a factory
            # that can create a perspective?
            perspective = IPerspective(factory_or_perspective, None)
            if perspective is None:
                perspective = factory_or_perspective()

            else:
                logger.warn(
                    'DEPRECATED: contribute perspective classes or '
                    'factories - not perspective instances.'
                )
                
            perspectives.append(perspective)
                
        return perspectives

    def _title_default(self):
        """ Trait initializer. """

        return self.workbench.application.name

    def _views_default(self):
        """ Trait initializer. """

        return [factory(window=self) for factory in self._views]
    
    ###########################################################################
    # 'WorkbenchWindow' interface.
    ###########################################################################

    def _action_sets_default(self):
        """ Trait initializer. """

        for item in self._actions:
            logger.warn(
                'DEPRECATED: ' \
                'use "enthought.envisage.ui.workbench.action_sets" '
                'not "enthought.envisage.ui.workbench.actions"'
            )
            
        action_sets = []
        for factory_or_action_set in self._action_sets + self._actions:
            if not isinstance(factory_or_action_set, ActionSet):
                action_set = factory_or_action_set(window=self)

            else:
                logger.warn(
                    'DEPRECATED: contribute action set classes or '
                    'factories - not action set instances.'
                )
                
                action_set = factory_or_action_set
                action_set.window = self
                
            action_sets.append(action_set)

        return action_sets

    ###########################################################################
    # 'IServiceRegistry' interface.
    ###########################################################################

    def get_service(self, protocol, query='', minimize='', maximize=''):
        """ Return at most one service that matches the specified query. """

        service = self.service_registry.get_service(
            protocol, query, minimize, maximize
        )

        return service

    def get_service_properties(self, service_id):
        """ Return the dictionary of properties associated with a service. """

        return self.service_registry.get_service_properties(service_id)
    
    def get_services(self, protocol, query='', minimize='', maximize=''):
        """ Return all services that match the specified query. """

        services = self.service_registry.get_services(
            protocol, query, minimize, maximize
        )

        return services

    def register_service(self, protocol, obj, properties=None):
        """ Register a service. """

        service_id = self.service_registry.register_service(
            protocol, obj, properties
        )

        return service_id

    def set_service_properties(self, service_id, properties):
        """ Set the dictionary of properties associated with a service. """

        self.service_registry.set_service_properties(service_id, properties)

        return

    def unregister_service(self, service_id):
        """ Unregister a service. """

        self.service_registry.unregister_service(service_id)

        return

    ###########################################################################
    # Private interface.
    ###########################################################################

    def __action_manager_builder_default(self):
        """ Trait initializer. """

        action_manager_builder = WorkbenchActionManagerBuilder(
            window=self, action_sets=self.action_sets
        )

        return action_manager_builder

    def _register_service_offers(self, service_offers):
        """ Register all service offers. """

        return map(self._register_service_offer, service_offers)

    def _register_service_offer(self, service_offer):
        """ Register a service offer. """

        # Add the window to the service offer properties (this is so that it
        # is available to the factory when it is called to create the actual
        # service).
        service_offer.properties['window'] = self

        service_id = self.register_service(
            protocol   = service_offer.protocol,
            obj        = service_offer.factory,
            properties = service_offer.properties
        )

        return service_id

    def _unregister_service_offers(self, service_ids):
        """ Unregister all service offers. """

        # Unregister the services in the reverse order that we registered
        # them.
        service_ids_copy = service_ids[:]
        service_ids_copy.reverse()
        
        for service_id in service_ids_copy:
            self.unregister_service(service_id)

        return
    
#### EOF ######################################################################
