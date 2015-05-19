"""
.. args.py

Argument parsing for applications.
"""

## Framework
import qpyapp.base

## Argument parsing
import argparse as ap
import pyslext.argparsing as arp


class ArgumentGroup(object):
    """ A command line argument group data holder. """
    def __init__(self, title, description=None):
        self.title = title
        self.description = description

    def __hash__(self):
        return hash(self.title)

    @property
    def kwargs(self):
        return {'title': self.title, 'description': self.description}


class Argument(object):
    """ A command line argument data holder. """
    def __init__(self, flags, action=None, nargs=None, const=None,
                 default=None, type=None, choices=None, required=None,
                 help=None, metavar=None, dest=None, version=None, proxy=None,
                 group=None):
        self.flags = flags
        self.action = action
        self.nargs = nargs
        self.const = const
        self.default = default
        self.type = type
        self.choices = choices
        self.required = required
        self.help = help
        self.metavar = metavar
        self.dest = dest
        self.version = version
        self.proxy = None
        self.group = group

    @property
    def args(self):
        return self.flags

    @property
    def kwargs(self):
        _kwargs = {}
        for key in ['action', 'nargs', 'const', 'default', 'type', 'choices',
                    'required', 'help', 'metavar', 'dest']:
            value = getattr(self, key)
            if value is None:
                continue
            _kwargs[key] = value

        return _kwargs


class ArgParser(qpyapp.base.Component):
    arguments = [
        Argument(("--key",), required=True)
    ]

    def __init__(self, app):
        ## Overload
        self.args = dict()
        app_cls = type(app)
        app_cls.parsed_args = property(lambda app: self.args)

        ## Get info from app
        ap_kwargs = dict()
        for attr in ['prog', 'description', 'epilog']:
            try:
                ap_kwargs[attr] = getattr(app, attr)
            except AttributeError:
                pass

        ## Initialize the arg parser
        argp = self.arg_parser = ap.ArgumentParser(
            formatter_class=arp.HelpFormatter, **ap_kwargs)

        ## Add arguments
        groups = dict()
        for arg in self.arguments:

            ## The argument is part of an argument group
            if arg.group:

                ## We already know that group
                try:
                  group = groups[arg.group.title]

                ## We have to add a new group
                except:
                  group = groups[arg.group.title] =\
                      argp.add_argument_group(**arg.group.kwargs)

            ## It is part of the "main" group
            else:
                group = argp

            ## Add the argument
            group.add_argument(*arg.args, **arg.kwargs)

        ## Get version from app
        try:
            version = app.version
        except AttributeError:
            pass
        else:
            argp.add_argument("-V", "--version", action='version',
                              version=version)

    def parse_args(self):
        """ Parse command line arguments, return a dictionary. """
        return dict(vars(self.arg_parser.parse_args()))

    def start(self):
        """ Parse args. """
        self.args = self.parse_args()

