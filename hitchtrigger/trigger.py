

class Trigger(object):
    def __init__(self, changes, exception_raised):
        self._changes = changes
        self._exception_raised = exception_raised

    def __bool__(self):
        changed = False
        for change in self._changes:
            change = changed or bool(change)
        return change or self._exception_raised

    def __nonzero__(self):
        return self.__bool__()
