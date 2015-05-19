"""
.. host.py

Host component for apps.
"""

## Framework
import app.base
import socket


class HostComp(app.base.Component):
    def __init__(self, app):
        ## Get git data
        self.hostname = socket.gethostname()

        ## Overload
        app_cls = type(app)
        app_cls.hostname = property(lambda app: self.hostname)

