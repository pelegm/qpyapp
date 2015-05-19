"""
.. loggers.py

Logging facilities for apps.
"""

## Logging proxy
__log_proxy__ = 1

## Framework
import qpyapp.base
import logging
logging.__log_proxy__ = 1
import sys
import datetime as dt
import inspect
import traceback

## Console
import pyslext.console as cns
import pygments as pyg
import pygments.lexers as pyglex
import pygments.formatters as pygfrmt
pytb = pyglex.get_lexer_by_name('pytb')
term = pygfrmt.get_formatter_by_name('terminal256')

## File handlers
import os
import errno


##################################
## ----- Module Constants ----- ##
##################################

DATE_FMT = "%Y%m%d-%H:%M:%S.%f"


############################
## ----- Log Levels ----- ##
############################

NOTSET = logging.NOTSET

DEBUG = logging.DEBUG
VERBOSE = 15
logging.addLevelName(VERBOSE, "VERBOSE")
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

level_pairs = ((0, NOTSET), (1, CRITICAL), (2, ERROR), (3, WARNING), (4, INFO),
               (5, VERBOSE), (6, DEBUG))

level_dict = dict(level_pairs)


def level_map(x):
    return level_dict.get(x, NOTSET)


########################
## ----- Daemon ----- ##
########################

class _LoggerDaemon(object):
    root_name = 'root'
    root_path = "."
    loglevel = NOTSET

    def setup(self, name=None, path=None, level=None):
        if name:
            self.root_name = name
        if path:
            self.root_path = path
        if level:
            self.loglevel = level


_logger_daemon = _LoggerDaemon()
setup = _logger_daemon.setup


#########################
## ----- Records ----- ##
#########################

class KWLogRecord(logging.LogRecord):
    def __init__(self, *args, **kwargs):
        super(KWLogRecord, self).__init__(*args, **kwargs)
        self.levelmark = self.levelname[0]
        self.func_name = "" if self.funcName == "<module>" else self.funcName

    def getMessage(self):
        """ Return the message for this LogRecord after merging any
        user-supplied arguments with the message. """
        ## All of the following is python's original code, but we assume
        ## unicode is always supported
        msg = self.msg
        if not isinstance(msg, basestring):
            try:
                msg = str(self.msg)
            except UnicodeError:
                msg = self.msg

        ## This is where we treat the record's 'args' differently
        ## We assume it is either a tuple containing one element, which is an
        ## empty dictionary (in which case no formatting should be made), or it
        ## is a non-empty dictionary (in which case formatting should be made)
        try:
            return msg.format(**self.args)
        except TypeError:
            return msg


############################
## ----- Formatters ----- ##
############################

class SimpleFormatter(logging.Formatter):
    template = "{r.levelmark} :: {r.asctime} :: {r.message}"
    pre_exc = ">>>\n"
    post_exc = "<<<"

    def __init__(self, datefmt):
        self.datefmt = "{{:{}}}".format(datefmt)

    def _line(self, record):
        record.message = record.getMessage()
        _dt = dt.datetime.fromtimestamp(record.created)
        record.asctime = self.datefmt.format(_dt)
        return self.template.format(r=record)

    def format_exception(self, exc_info):
        return "".join(traceback.format_exception(*exc_info))

    def formatException(self, exc_info):
        return self.pre_exc + self.format_exception(exc_info) + self.post_exc

    def format(self, record):
        ## Formatting message
        s = self._line(record)

        ## Formatting exceptions
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            if s[-1:] != "\n":
                s += "\n"
            try:
                s = s + exc_text
            except UnicodeError:
                s = s + exc_text.decode(sys.getfilesystemencoding(), 'replace')

        return s


class ColorFormatter(SimpleFormatter):
    _xcolor_code_map = dict(D=37, V=33, I=61, W=125, E=160, C=160, dt=241,
                            s=240)
    _xcolor_map = dict((k, cns.xcolor(v))
                       for k, v in _xcolor_code_map.viewitems())
    _xcolor_map['N'] = cns.nocolor()

    template = "{{{r.levelmark}}}{{r.levelmark}}{{N}}" +\
        "{{s}} :: {{N}}{{dt}}{{r.asctime}}{{N}}" +\
        "{{s}} :: {{N}}{{{r.levelmark}}}{{r.message}}{{N}}"

    def _line(self, record):
        s = super(ColorFormatter, self)._line(record)
        try:
            return s.format(r=record, **self._xcolor_map)
        except IndexError:
            raise ValueError(s)

    def format_exception(self, exc_info):
        exc = super(ColorFormatter, self).format_exception(exc_info)
        return pyg.highlight(exc, lexer=pytb, formatter=term)


## TODO: temporary
class FullFormatter(SimpleFormatter):
    template = "{r.levelmark} :: {r.asctime}" +\
        " :: {r.module}.{r.func_name}:{r.lineno} :: {r.message}"


##########################
## ----- Handlers ----- ##
##########################

class PromptHandler(logging.Handler):
    def emit(self, record):
        try:
            prompt = self.prompt
        except AttributeError:
            pass
        else:
            message = self.format(record)
            prompt(message)


##############################
## ----- Logger Proxy ----- ##
##############################


class Logger(logging.getLoggerClass()):
    UNKNOWN_FILE = "(unknown file)"
    UNKNOWN_FUNC = "(unknown function)"

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None,
                   extra=None):
        """ A factory method for creation of KWLogRecords. """
        rec = KWLogRecord(name, level, fn, lno, msg, args, exc_info, func)
        if extra is not None:
            for key in extra:
                if (key in ["message", "asctime"]) or (key in rec.__dict__):
                    raise KeyError("Attempt to overwrite %r in LogRecord"
                                   % key)
                rec.__dict__[key] = extra[key]
        return rec

    def findCaller(self):
        ## Loop until a frame which is not a logging proxy is found
        frame = inspect.currentframe()
        while ('__log_proxy__' in frame.f_globals
               or '__log_proxy__' in frame.f_locals):
            frame = frame.f_back

        try:
            code = frame.f_code
        except AttributeError:
            return self.UNKNOWN_FILE, 0, self.UNKNOWN_FUNC

        return code.co_filename, frame.f_lineno, code.co_name

    def _log(self, level, msg, args, exc_info=None, extra=None):
        ## This is a log proxy
        _log_proxy, = True,

        try:
            fn, lno, func = self.findCaller()
        except ValueError:
            fn, lno, func = self.UNKNOWN_FILE, 0, self.UNKNOWN_FUNC

        if exc_info:
            if not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()

        record = self.makeRecord(self.name, level, fn, lno, msg, args,
                                 exc_info, func, extra)
        self.handle(record)


logging.setLoggerClass(Logger)


class LoggerProxy(object):
    def __init__(self, logger):
        self.logger = logger

    def add_handler(self, handler):
        self.logger.addHandler(handler)

    def set_level(self, level):
        self.logger.setLevel(level)

    def debug(self, msg, **kwargs):
        self.log(DEBUG, msg, **kwargs)

    def verbose(self, msg, **kwargs):
        self.log(VERBOSE, msg, **kwargs)

    def info(self, msg, **kwargs):
        self.log(INFO, msg, **kwargs)

    def warning(self, msg, **kwargs):
        self.log(WARNING, msg, **kwargs)

    def error(self, msg, **kwargs):
        self.log(ERROR, msg, **kwargs)

    def critical(self, msg, **kwargs):
        self.log(CRITICAL, msg, **kwargs)

    def log(self, level, msg, exc_info=None, **kwargs):
        _args = (kwargs,)
        _kwargs = dict(exc_info=exc_info)

        ## We turn **kwargs into a sole *arg
        ## If kwargs is a non-empty dictionary, it will become record.args
        ## If kwargs is an empty dictionary, record.args will be a tuple
        ## containing that empty dictionary
        ## This is a consequence of python's logging internals
        self.logger.log(level, msg, *_args, **_kwargs)

    def close(self):
        for handler in self.logger.handlers:
            handler.close()

        ## According to this recommendation:
        ## https://mail.python.org/pipermail/python-list/2011-June/606610.html
        del logging.Logger.manager.loggerDict[self.logger.name]


###################################
## ----- Formatter Factory ----- ##
###################################

## We initialize instantiated formatters dictionary; this will hold the
## instantiated formatters, so they will not be have to initialized twice
_instantiated_formatters = dict()


_formatter_klass_map = dict(
    simple=SimpleFormatter,
    color=ColorFormatter,
    full=FullFormatter,
)


def get_formatter(name, klass, **kwargs):
    """ A factory for python's logging formatters. """
    ## We first check whether the formatter was already instantiated
    try:
        return _instantiated_formatters[name]

    ## This is the first call to this handler
    except KeyError:
        pass

    ## Create formatter using the appropriate factory
    factory = _formatter_klass_map[klass]
    formatter = factory(**kwargs)

    ## Keep formatter
    _instantiated_formatters[name] = formatter

    ## Return formatter
    return formatter


#################################
## ----- Handler Factory ----- ##
#################################

## We initialize instantiated handlers dictionary; this will hold the
## instantiated handlers, so they will not be have to initialized twice
_instantiated_handlers = dict()


def _get_prompt_handler(prompt, color=False):
    ## Instantiate a prompt handler
    handler = PromptHandler()

    ## Set its prompt
    handler.prompt = prompt

    ## Set simple / color formatter for handler
    if not color:
        formatter = get_formatter('simple', 'simple', datefmt=DATE_FMT)
    else:
        formatter = get_formatter('color', 'color', datefmt=DATE_FMT)
    handler.setFormatter(formatter)

    ## Return handler
    return handler


def _get_file_handler(filename):
    """ Instantiate and return a file handler for *filename*. Create all
    necessary paths. """
    ## Create all necessary paths
    dirname = os.path.dirname(filename)
    try:
        os.makedirs(dirname)
    except OSError as os_err:
        if os_err.errno != errno.EEXIST:
            raise

    ## Instantiate handler
    handler = logging.FileHandler(filename)

    ## Set full formatter for handler
    formatter = get_formatter('full', 'full', datefmt=DATE_FMT)
    handler.setFormatter(formatter)

    ## Return handler
    return handler


_handler_klass_map = dict(
    prompt=_get_prompt_handler,
    file=_get_file_handler,
)


def get_handler(name, klass, level, **kwargs):
    """ A factory for python's logging handlers. """
    ## We first check whether the handler was already instantiated
    try:
        return _instantiated_handlers[name]

    ## This is the first call to this handler
    except KeyError:
        pass

    ## Create handler using the appropriate factory
    factory = _handler_klass_map[klass]
    handler = factory(**kwargs)
    handler.setLevel(level)

    ## Keep handler
    _instantiated_handlers[name] = handler

    ## Return handler
    return handler


################################
## ----- Logger Factory ----- ##
################################

## We initialize instantiated loggers dictionary; this will hold the
## instantiated loggers, so they will not be have to initialized twice
_instantiated_loggers = dict()


def get_logger(name, level=DEBUG, prompt=None, color=None, relpath=None):
    """ A proxy for python's logging.getLogger, which also prepares handlers,
    formatters, etc.

    A valid logger name is either '/' for the root logger, or /base, or
    /category/base or /category/base.id. Similarly, /category/subcat/base[.id]
    is valid, and this can be nested. The first '/' is optional, and will added
    if not given. """
    ## If / does not prefix the name, we add it
    if not name[0] == "/":
        name = "/" + name

    ## We check whether the logger was already instantiated
    try:
        return _instantiated_loggers[name]

    ## This is the first call to this logger
    except KeyError:
        pass

    ## Find real logger name
    _name = name[1:]
    if not _name:
        real_logger_name = _logger_daemon.root_name
    else:
        real_logger_name = _logger_daemon.root_name + "." +\
            _name.replace("/", ".")

    ## Get real logger
    real_logger = logging.getLogger(real_logger_name)

    ## Overload logger
    logger = LoggerProxy(real_logger)

    ## Keep logger
    _instantiated_loggers[name] = logger

    ## Get+Set file handler
    if not _name:
        _name = _logger_daemon.root_name
    filename = os.path.join(_logger_daemon.root_path, _name) + ".log"
    file_handler_name = "file://" + filename
    file_handler = get_handler(file_handler_name, "file", level=level,
                               filename=filename)
    logger.add_handler(file_handler)

    ## Get+Set prompt handler
    if prompt:
        prompt_handler_name = "color_" * color + "prompt"
        prompt_handler = get_handler(prompt_handler_name, "prompt",
                                     level=level, prompt=prompt, color=color)
        logger.add_handler(prompt_handler)

    ## Set log level
    logger.set_level(level)

    ## Return logger
    return logger


################################
## ----- Main Component ----- ##
################################

class SimpleLogger(qpyapp.base.Component):
    """ The simple logger overloads the app with debug/info/warn/error/critical
    methods for logging, where the handler is the app's prompt method. """
    def __init__(self, app):
        self.app = app

    def start(self):
        ## Set logger
        loglevel = self.app_loglevel()
        logpath = self.app_logpath()
        _logger_daemon.setup(name=self.app.name, path=logpath, level=loglevel)
        color_prompt = getattr(self.app, 'color_prompt', False)
        self.logger = get_logger("/", level=loglevel, prompt=self.app.prompt,
                                 color=color_prompt)

        ## Overload app
        self.app.debug = self.logger.debug
        self.app.verbose = self.logger.verbose
        self.app.info = self.logger.info
        self.app.warning = self.logger.warning
        self.app.error = self.logger.error
        self.app.critical = self.logger.critical
        self.app.loglevel = loglevel

        ## Log
        self.logger.info("Logger for app is set.")

    def app_loglevel(self):
        verbosity = self.app.parsed_args.get('verbosity', 0)
        return level_dict[verbosity]

    def app_logpath(self):
        return self.app.parsed_args.get('logpath', ".")

    def handle_error(self, app):
        exc_info = sys.exc_info()
        tb = ''.join(traceback.format_exception(*exc_info))
        msg = "Application Failure:\n>>>\n{tb}<<<"
        app.critical(msg, tb=tb)

