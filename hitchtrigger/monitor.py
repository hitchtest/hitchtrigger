from hitchtrigger import models
from hitchtrigger.watch import Watch


class Monitor(object):
    def __init__(self, sqlite_filename):
        models.use_sqlite_db(sqlite_filename)

    def watch(self, blockname, files=None, flags=None):
        assert type(blockname) is str
        files = [] if files is None else files
        flags = {} if flags is None else flags
        return Watch(self, blockname, files, flags)
