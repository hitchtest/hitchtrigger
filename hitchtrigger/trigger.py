

class Trigger(object):
    def __init__(
        self,
        unmonitored_files,
        modified_files,
        modified_flags,
        new_flags,
        exception_raised
    ):
        self._unmonitored_files = unmonitored_files
        self._modified_files = modified_files
        self._modified_flags = modified_flags
        self._new_flags = new_flags
        self._exception_raised = exception_raised

    def __bool__(self):
        return len(self._unmonitored_files) > 0 or \
               len(self._modified_files) > 0 or \
               len(self._modified_flags) > 0 or \
               len(self._new_flags) > 0 or \
               self._exception_raised

    def __nonzero__(self):
        return self.__bool__()
