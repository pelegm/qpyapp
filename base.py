"""
.. abstract.py

Generalising the application concept.
"""


#############################
## ----- Application ----- ##
#############################

class Application(object):
    """ An app has 3 stages of life: **init**, which is the pure initialisation
    of the python object and all related python objects; **start**, which
    setups the system, including all needed configurations, which may need to
    connect to remote objects, read user input, etc.; and **run**, which starts
    the main operation of the app. An *app* should also have an **exit**
    method, which should be called automatically when the run ends, either
    properly or with an exception. """
    _comp_classes = []

    def __init__(self):
        ## Initialise the components
        self.components = []
        for comp_cls in self._comp_classes:
            self.components.append(comp_cls(self))

        ## Init
        self.started = False

    def prompt(self, msg):
        print msg

    def handle_error(self, exit=True):
        for component in self.components:
            component.handle_error(self)

        if exit:
            self.exit()

    def start(self):
        for component in self.components:
            component.start()
        self.started = True
        self.running = False

    def run(self):
        self.running = True
        self.running = False
        self.exit()

    def exit(self):
        ## We exit in an opposite order
        for component in reversed(self.components):
            component.exit()


###########################
## ----- Component ----- ##
###########################

class Component(object):
    """ An application may have a list of components. The order of the
    occurrence of the components may have effect on their precedence. Each
    component has 'hooks' which are being called by the proper order in the
    proper places.

    The component list is an attribute of the class, not of a class instance.
    That means, the addition of components to a class may alter its properties,
    methods, and in particular, it defines its signature. """
    def __init__(self, app):
        pass

    def handle_error(self, app):
        pass

    def start(self):
        pass

    def exit(self):
        pass

