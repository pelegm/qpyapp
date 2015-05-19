"""
.. eventdriven.py

An event-driven application framework.
"""

## Framework
import qpyapp.base

## Prompting
import pyslext.console as cns


class DummyEngine(object):
    pass


class EventDrivenApplication(qpyapp.base.Application):
    engine_class = None
    engine_kwargs = {}

    color_prompt = True

    ## Prompting
    def prompt(self, msg, fail=False, success=False):
        if success:
            msg = cns.color('green', bold=True) + msg + cns.nocolor()
        elif fail:
            msg = cns.color('red', bold=True) + msg + cns.nocolor()

        try:
            engine = self.engine
        except AttributeError:
            pass
        else:
            ## The engine is using the term; we will not use it ourselves
            if engine.using_term:

                ## Prompt via the engine
                self.engine.prompt(msg)
                return

        print msg

    ## Engine error handling
    def _handle_engine_error(self):
        msg = "Event-driven app could not start engine."
        self.prompt(msg, fail=True)
        self.handle_error()

    ## App error handling
    def _handle_app_error(self):
        msg = "Application failure."
        self.prompt(msg, fail=True)
        exit = False
        self.handle_error(exit=exit)

    def process(self):
        pass

    def nodata(self, count):
        pass

    def stop(self):
        print "Event-Driven App is stopping."
        self.running = False
        if self._engine_on:
            print "Closing engine"
            self.engine.close()
            self.prompt("Engine has stopped.")
            self._engine_on = False

    def start(self):
        super(EventDrivenApplication, self).start()

        self._engine_on = False

        ## Prepare the engine
        try:
            self.engine = self.engine_class(**self.engine_kwargs)
        except StandardError:
            self._handle_engine_error()
            self.started = False
            return
        else:
            self._engine_on = True

        self.prompt("Engine has started! ({})".format(self.engine.details),
                    success=True)

    def run(self):
        if not self.started:
            return self.exit()

        self.running = True
        _nodata_counter = 0

        ## Run loop
        while self.running:

            ## Loop over the events
            try:

                ## As long as there's data, we'll be inside that loop
                for event in self.engine:

                    _nodata_counter = 0
                    try:
                        self.process(event)
                    except StandardError:
                        self._handle_app_error()

            ## User wishes to stop?
            except KeyboardInterrupt:
                self.prompt("\n\nCtrl-C")
                self.running = False

            ## Engine is off
            except self.engine.Off:
                self.prompt("\n\nEngine is off.")
                self.running = False

            else:
                ## User has not wished to abort, but there's no data
                ## The app should do something about it
                ## Currently, it doesn't mean we're not running any more
                _nodata_counter += 1
                self.nodata(_nodata_counter)

        print "Done; going to exit app."
        self.exit()

    def exit(self):
        print "Exiting app."
        try:
            engine = self.engine
        except AttributeError:
            print "I HAVE NO ENGINE!!!"
            return

        if self._engine_on:
            print "Closing engine"
            engine.close()
            self.prompt("Engine has stopped.")
            self._engine_on = False

        print "Hopefully, engine is closed; nothing should run any more."
        self.prompt("You may need to press enter, and/or wait a few seconds.")

