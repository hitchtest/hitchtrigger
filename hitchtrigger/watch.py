from hitchtrigger.trigger import Trigger
from hitchtrigger import models
from os import path


HOW_TO_USE_WATCHER = """\
You cannot treat watcher as a boolean.

It must be used as a context manager.
"""


class Watch(object):
    def __init__(self, monitor, blockname, files, flags):
        self.monitor = monitor
        self.blockname = blockname
        self.files = [path.abspath(filename) for filename in files]
        self.flags = flags

        if models.Watch.filter(name=blockname).first() is None:
            self.watch_model = models.Watch(name=blockname, exception_raised=False)
            self.watch_model.save(force_insert=True)
        else:
            self.watch_model = models.Watch.filter(name=blockname).first()

    def __enter__(self):
        new_flags = list(self.flags.keys())
        changed_flags = []

        for flag in models.Flag.filter(watch=self.watch_model):
            if flag.name in self.flags:
                new_flags.remove(flag.name)
                if self.flags[flag.name] != flag.value:
                    changed_flags.append(flag.name)
                    flag.value = self.flags[flag.name]
                    flag.save()
            else:
                new_flags.remove(flag.name)

        for flag in new_flags:
            flag_model = models.Flag(watch=self.watch_model, name=flag, value=self.flags[flag])
            flag_model.save()

        new_files = list(self.files)
        modified_files = []

        for monitored_file in models.File.filter(watch=self.watch_model):
            filename = monitored_file.filename
            if filename in self.files:
                new_files.remove(filename)

                if path.getmtime(filename) > monitored_file.last_modified:
                    modified_files.append(filename)
                    monitored_file.last_modified = path.getmtime(filename)
                    monitored_file.save()

        for filename in new_files:
            file_model = models.File(
                watch=self.watch_model,
                filename=filename,
                last_modified=path.getmtime(filename),
            )
            file_model.save()

        return Trigger(
            new_files,
            modified_files,
            new_flags,
            changed_flags,
            self.watch_model.exception_raised
        )

    def __exit__(self, type, value, traceback):
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
