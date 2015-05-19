"""
.. host.py

Host component for apps.
"""

## Framework
import qpyapp.base
import socket


class HostComp(qpyapp.base.Component):
    def __init__(self, app):
        ## Get git data
        self.hostname = socket.gethostname()

        ## Overload
        app_cls = type(app)
        app_cls.hostname = property(lambda app: self.hostname)

