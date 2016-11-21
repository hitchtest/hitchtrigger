

class Trigger(object):
    def __init__(self, changes, exception_raised, override):
        self._changes = changes
        self._exception_raised = exception_raised
        self._override = override

    def __bool__(self):
        changed = False
        for change in self._changes:
            change = changed or bool(change)
        return change or self._exception_raised or self._override

    def __nonzero__(self):
        return self.__bool__()

    @property
    def why(self):
        contents = ""

        for change in self._changes:
            contents = contents + change.why

        if self._exception_raised:
            contents += "Exception occurred on last run.\n"

        if self._override:
            contents += "Manually triggered via override.\n"

        return contents
