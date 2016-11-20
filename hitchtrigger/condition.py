from os import path as ospath
from hitchtrigger import exceptions
from hitchtrigger import models
import datetime
import humanize
import pickle
import base64
import copy


class Change(object):
    def __nonzero__(self):
        return self.__bool__()


class NoChange(Change):
    def __bool__(self):
        return False


class YesChange(Change):
    def __init__(self, message):
        self._message = message

    @property
    def why(self):
        return self._message

    def __bool__(self):
        return True


class TimeElapsedChange(Change):
    def __init__(self, last_run, duration):
        self._last_run = last_run
        self._duration = duration

    @property
    def why(self):
        return "Should run every time {0} elapses and {1} elapsed.".format(
            humanize.naturaldelta(self._duration),
            humanize.naturaldelta(datetime.datetime.now() - self._last_run),
        )

    def __bool__(self):
        return True


class DependentWatchChange(Change):
    def __init__(self, name):
        self._name = name

    @property
    def why(self):
        return "Dependent watch '{0}' was triggered.".format(self._name)

    def __bool__(self):
        return True


class FileChange(Change):
    def __init__(self, new, modified):
        self._new = new
        self._modified = modified

    @property
    def why(self):
        contents = ""
        if len(self._new) > 0:
            contents += "New file(s) / director(ies) detected:\n"
            for new in self._new:
                contents += "  - {0}\n".format(new)
        if len(self._modified) > 0:
            contents += "File(s) / director(ies) changed:\n"
            for modified in self._modified:
                contents += "  - {0}\n".format(modified)
        return contents

    def __bool__(self):
        return len(self._new) > 0 or len(self._modified) > 0


class VarChange(Change):
    def __init__(self, new, modified, original):
        self._new = new
        self._modified = modified
        self._original = original

    @property
    def why(self):
        contents = ""
        if len(self._new) > 0:
            contents += "New monitored var(s) detected:\n"
            for name, value in self._new.items():
                contents += "  - {0} = {1}\n".format(name, value)
        if len(self._modified) > 0:
            contents += "Modified monitored var(s) detected:\n"
            for name, value in self._modified.items():
                contents += "  - {0} was:\n      {1}\n    is now\n      {2}\n".format(
                    name, self._original[name], value
                )
        return contents

    def __bool__(self):
        return len(self._new) > 0 or len(self._modified) > 0


class NonexistentChange(Change):
    def __init__(self, path):
        self._path = path

    def __bool__(self):
        return not ospath.exists(self._path)


class Condition(object):
    def __init__(self):
        self._other_condition = None

    def __or__(self, other):
        self._other_condition = other
        return self

    def all_conditions(self):
        conditions = [self, ]
        other_condition = self._other_condition

        while other_condition is not None:
            conditions.append(other_condition)
            other_condition = other_condition._other_condition
        return conditions


class Modified(Condition):
    def __init__(self, monitor, paths):
        self._monitor = monitor
        self._paths = paths
        super(Modified, self).__init__()

    def check(self, watch_model):
        new_files = list(self._paths)
        modified_files = []

        for monitored_file in models.File.filter(watch=watch_model):
            filename = monitored_file.filename
            if filename in self._paths:
                new_files.remove(filename)

                if ospath.getmtime(filename) > monitored_file.last_modified:
                    modified_files.append(filename)
                    monitored_file.last_modified = ospath.getmtime(filename)
                    monitored_file.save()

        for filename in new_files:
            file_model = models.File(
                watch=watch_model,
                filename=filename,
                last_modified=ospath.getmtime(filename),
            )
            file_model.save()

        return FileChange(new_files, modified_files)


class Var(Condition):
    def __init__(self, monitor, kwargs):
        self._monitor = monitor
        self._vars = kwargs
        super(Var, self).__init__()

    def check(self, watch_model):
        new_vars = copy.copy(self._vars)
        changed_vars = {}
        original_vars = {}

        for var in models.Var.filter(watch=watch_model):
            if var.name in self._vars.keys():
                del new_vars[var.name]
                if self._vars[var.name] != pickle.loads(base64.b64decode(var.value)):
                    changed_vars[var.name] = self._vars[var.name]
                    original_vars[var.name] = pickle.loads(base64.b64decode(var.value))
                    var.value = self._vars[var.name]
                    var.save()

        for var, value in new_vars.items():
            var_model = models.Var(
                watch=watch_model, name=var,
                value=base64.b64encode(pickle.dumps(self._vars[var]))
            )
            var_model.save()

        return VarChange(new_vars, changed_vars, original_vars)


class Nonexistent(Condition):
    def __init__(self, path):
        super(Nonexistent, self).__init__()
        self._path = path

    def check(self, _):
        return NonexistentChange(self._path)


class NotRunSince(Condition):
    def __init__(self, monitor, timedelta):
        super(NotRunSince, self).__init__()
        self._monitor = monitor
        self._timedelta = timedelta

    def check(self, watch_model):
        if watch_model.last_run is None:
            return YesChange("Never run.")

        if watch_model.last_run + self._timedelta < datetime.datetime.now():
            return TimeElapsedChange(watch_model.last_run, self._timedelta)
        else:
            return NoChange()


class WasRun(Condition):
    def __init__(self, monitor, name):
        super(WasRun, self).__init__()
        self._monitor = monitor
        self._name = name

    def check(self, watch_model):
        dependent_model = models.Watch.filter(name=self._name).first()

        if dependent_model is None:
            raise exceptions.DependentModelNotFound(
                "Dependent model '{0}' not found.".format(self._name)
            )

        was_triggered = dependent_model.was_triggered_on_last_run

        if was_triggered is None or was_triggered is True:
            return DependentWatchChange(self._name)
        else:
            return NoChange()
