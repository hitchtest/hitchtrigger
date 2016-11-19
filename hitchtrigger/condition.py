from os import path as ospath
from hitchtrigger import exceptions
from hitchtrigger import models
import datetime
import pickle
import base64


class Change(object):
    def __nonzero__(self):
        return self.__bool__()


class NoChange(Change):
    def __bool__(self):
        return False


class YesChange(Change):
    def __bool__(self):
        return True


class TimeElapsedChange(Change):
    def __init__(self, since, duration):
        self._since = since
        self._duration = duration

    def __bool__(self):
        return True


class FileChange(Change):
    def __init__(self, new, modified):
        self._new = new
        self._modified = modified

    def __bool__(self):
        return len(self._new) > 0 or len(self._modified) > 0


class VarChange(Change):
    def __init__(self, new, modified):
        self._new = new
        self._modified = modified

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
        new_vars = [str(var) for var in self._vars.keys()]
        changed_vars = []

        for var in models.Var.filter(watch=watch_model):
            if var.name in self._vars.keys():
                new_vars.remove(str(var.name))
                if self._vars[var.name] != pickle.loads(base64.b64decode(var.value)):
                    changed_vars.append(var.name)
                    var.value = self._vars[var.name]
                    var.save()

        for var in new_vars:
            var_model = models.Var(
                watch=watch_model, name=var,
                value=base64.b64encode(pickle.dumps(self._vars[var]))
            )
            var_model.save()

        return VarChange(new_vars, changed_vars)


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
            return YesChange()

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

        if watch_model.last_run is None or dependent_model.last_run is None:
            return YesChange()

        if watch_model.last_run > dependent_model.last_run:
            return YesChange()

        return NoChange()
