from hitchtrigger import models
from hitchtrigger.watch import Watch
from hitchtrigger.condition import Modified, Var, Nonexistent, NotRunSince, WasRun
from datetime import timedelta as python_timedelta


class Monitor(object):
    def __init__(self, sqlite_filename):
        models.use_sqlite_db(sqlite_filename)

    def watch(self, blockname, condition):
        return Watch(blockname, condition)

    def modified(self, paths):
        """
        Create a Condition that triggers when a file or directory
        in a list (or other iterable) of paths has changed.
        """
        return Modified(self, paths)

    def var(self, **kwargs):
        """
        Create a condition that triggers when one of the variables
        fed via kwargs has changed.
        """
        return Var(self, kwargs)

    def nonexistent(self, path):
        """
        Conditions that triggers when a path (file or directory)
        is found to be non-existent.
        """
        return Nonexistent(path)

    def not_run_since(self, seconds=0, minutes=0, hours=0, days=0, timedelta=None):
        """
        Condition that triggers when a period of time has elapsed since
        last run.
        """
        td = python_timedelta()
        if timedelta is not None:
            assert type(timedelta) is python_timedelta
            td = td + timedelta
        td = td + python_timedelta(seconds=seconds)
        td = td + python_timedelta(minutes=minutes)
        td = td + python_timedelta(hours=hours)
        td = td + python_timedelta(days=days)
        return NotRunSince(self, td)

    def was_run(self, name):
        """
        Condition that triggers when a previous block was just triggered.
        """
        return WasRun(self, name)
