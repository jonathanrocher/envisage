""" An action in a menu bar, menu, or tool bar. """


# Enthought library imports.
from enthought.traits.api import Str

# Local imports.
from location import Location


class Action(Location):
    """ An action in a menu bar, menu, or tool bar. """

    #### Action implementation ################################################

    # The action's name (appears on menus and toolbars etc).
    name = Str

    # The name of the class that implements the action.
    class_name = Str

    ###########################################################################
    # 'object' interface
    ###########################################################################
    
    def __str__(self):
        """ Return the 'informal' string representation of the object. """

        return 'Action(%s)' % self.class_name

    __repr__ = __str__
    
#### EOF ######################################################################
