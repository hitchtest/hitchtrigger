from os import path as ospath
from hitchtrigger import models
import datetime



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


class FlagChange(Change):
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


class Flag(Condition):
    def __init__(self, monitor, flags):
        self._monitor = monitor
        self._flags = flags
        super(Flag, self).__init__()

    def check(self, watch_model):
        new_flags = list(self._flags.keys())
        changed_flags = []

        for flag in models.Flag.filter(watch=watch_model):
            if flag.name in self._flags:
                new_flags.remove(flag.name)
                if self._flags[flag.name] != flag.value:
                    changed_flags.append(flag.name)
                    flag.value = self._flags[flag.name]
                    flag.save()

        for flag in new_flags:
            flag_model = models.Flag(watch=watch_model, name=flag, value=self._flags[flag])
            flag_model.save()

        return FlagChange(new_flags, changed_flags)


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
            raise RuntimeError("Dependent model {0} not found".format(self._name))

        if watch_model.last_run is None or dependent_model.last_run is None:
            return YesChange()

        if watch_model.last_run > dependent_model.last_run:
            return YesChange()

        return NoChange()
