from peewee import ForeignKeyField, CharField, FloatField, BooleanField, DateTimeField, TextField
from peewee import SqliteDatabase, Model
from datetime import timedelta as python_timedelta
from hitchtrigger.block import Block
from hitchtrigger import condition
from hitchtrigger import exceptions
import pickle


class Monitor(object):
    def __init__(self, sqlite_filename):
        class BaseModel(Model):
            class Meta:
                database = SqliteDatabase(sqlite_filename)

        class Watch(BaseModel):
            name = CharField(primary_key=True)
            exception_raised = BooleanField()
            last_run = DateTimeField(null=True)
            was_triggered_on_last_run = BooleanField(null=True)

        class File(BaseModel):
            watch = ForeignKeyField(Watch)
            filename = CharField(max_length=640)
            last_modified = FloatField()

        class Var(BaseModel):
            watch = ForeignKeyField(Watch)
            name = CharField(max_length=256)
            value = TextField()

        if not Watch.table_exists():
            Watch.create_table()
        if not File.table_exists():
            File.create_table()
        if not Var.table_exists():
            Var.create_table()

        self.BaseModel = BaseModel
        self.File = File
        self.Watch = Watch
        self.Var = Var

    def block(self, name, condition):
        return Block(self, name, condition)

    def modified(self, paths):
        """
        Create a Condition that triggers when a file or directory
        in a list (or other iterable) of paths has changed.
        """
        return condition.Modified(self, paths)

    def var(self, **kwargs):
        """
        Create a condition that triggers when one of the variables
        fed via kwargs has changed.
        """
        for key, value in kwargs.items():
            assert type(key) is str

            try:
                pickle.dumps(value)
            except TypeError:
                raise exceptions.VarMustBePickleable("Can't use non-pickleable objects as vars.")
        return condition.Var(self, kwargs)

    def nonexistent(self, path):
        """
        Returns conditions that triggers when a path (file or directory)
        is found to be non-existent.
        """
        return condition.Nonexistent(path)

    def not_run_since(self, seconds=0, minutes=0, hours=0, days=0, timedelta=None):
        """
        Returns condition that triggers when a period of time has elapsed since
        last run.

        All parameters are added together.
        - seconds, minutes, hours days are integers
        - timedelta is a python timedelta object
        """
        td = python_timedelta()
        if timedelta is not None:
            assert type(timedelta) is python_timedelta
            td = td + timedelta
        td = td + python_timedelta(seconds=seconds)
        td = td + python_timedelta(minutes=minutes)
        td = td + python_timedelta(hours=hours)
        td = td + python_timedelta(days=days)
        return condition.NotRunSince(self, td)

    def was_run(self, name):
        """
        Condition that triggers when a previous block was just triggered.
        """
        return condition.WasRun(self, name)
