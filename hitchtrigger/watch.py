from hitchtrigger.trigger import Trigger
from hitchtrigger import models
from os import path
import datetime


HOW_TO_USE_WATCHER = """\
You cannot treat watcher as a boolean.

It must be used as a context manager.
"""


class Watch(object):
    def __init__(self, blockname, condition):
        self._blockname = blockname
        self._condition = condition

        if models.Watch.filter(name=blockname).first() is None:
            self.watch_model = models.Watch(name=blockname, exception_raised=False, last_run=None)
            self.watch_model.save(force_insert=True)
        else:
            self.watch_model = models.Watch.filter(name=blockname).first()

    def __enter__(self):
        changes = []
        for condition in self._condition.all_conditions():
            change = condition.check(self.watch_model)
            changes.append(change)
        return Trigger(changes, self.watch_model.exception_raised)

    def __exit__(self, type, value, traceback):
        self.watch_model.last_run = datetime.datetime.now()
        if traceback is not None:
            self.watch_model.exception_raised = True
            self.watch_model.save()
        else:
            self.watch_model.exception_raised = False
            self.watch_model.save()

    def __bool__(self):
        raise NotImplementedError(HOW_TO_USE_WATCHER)

    def __nonzero__(self):
        raise NotImplementedError(HOW_TO_USE_WATCHER)
