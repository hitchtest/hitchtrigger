from hitchtrigger.trigger import Trigger
from hitchtrigger import models
import datetime


class HitchTriggerBlockContextManager(object):
    def __init__(self, block):
        self._block = block

    @property
    def model(self):
        return self._block.watch_model

    def __enter__(self):
        changes = []
        for condition in self._block._condition.all_conditions():
            change = condition.check(self.model)
            changes.append(change)
        trigger = Trigger(changes, self.model.exception_raised)

        self.model.was_triggered_on_last_run = bool(trigger)
        self.model.save()
        return trigger

    def __exit__(self, type, value, traceback):
        self.model.last_run = datetime.datetime.now()
        if traceback is not None:
            self.model.exception_raised = True
            self.model.save()
        else:
            self.model.exception_raised = False
            self.model.save()

    def __bool__(self):
        raise NotImplementedError("Must use .context() as context manager")

    def __nonzero__(self):
        raise self.__bool__()


class Block(object):
    def __init__(self, blockname, condition):
        self._blockname = blockname
        self._condition = condition

        if models.Watch.filter(name=blockname).first() is None:
            self.watch_model = models.Watch(
                name=blockname,
                exception_raised=False,
                last_run=None,
                was_triggered_on_last_run=None
            )
            self.watch_model.save(force_insert=True)
        else:
            self.watch_model = models.Watch.filter(name=blockname).first()

    def context(self):
        return HitchTriggerBlockContextManager(self)
