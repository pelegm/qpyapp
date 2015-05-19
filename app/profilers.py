"""
.. profilers.py

Profiling facilities for apps.
"""

## Framework
import app.base
import cProfile as profile
import subprocess as sp
import types


class Profiler(app.base.Component):
    """ The :class:`Profiler` component wrap's the run method of its app with
    profiling facilities. If the app has a *prof_fname* attribute, it saves the
    stats to that file. If it also has a *prof_img_fname* attribute, is creates
    a profile image at that path.

    To make profiling optional, the component looks for *profile* attribute of
    the app. It only profiles if it finds one and it is ``True``. """
    def __init__(self, app):
        ## Instantiate a profiler
        self.profiler = profile.Profile()

        ## Wrap the app's run method
        app._profiled_run = app.run

        def run(app, profiler=self.profiler):
            if not getattr(app, 'profile', False):
                app._profiled_run()
                return

            app.info("Start profiling...")
            profiler.enable()
            app._profiled_run()
            profiler.disable()
            app.info("End profiling...")

            ## Dump stats
            try:
                prof_fname = app.prof_fname
            except AttributeError:
                pass
            else:
                app.info("Dumping profile stats...")
                profiler.dump_stats(prof_fname)

            ## Plot stats
            try:
                prof_fname = app.prof_fname
                prof_img_fname = app.prof_img_fname
            except AttributeError:
                pass
            else:
                app.info("Plotting profile stats...")
                gprof_cmd = ['gprof2dot', '-f', 'pstats', prof_fname]
                dot_cmd = ['dot', '-T', 'png', '-o', prof_img_fname]
                gprof_proc = sp.Popen(gprof_cmd, stdout=sp.PIPE)
                try:
                    sp.check_call(dot_cmd, stdin=gprof_proc.stdout)
                    gprof_proc.wait()
                except sp.CalledProcessError:
                    self.error("gprof2dot has failed.")

        app.run = types.MethodType(run, app, type(app))

