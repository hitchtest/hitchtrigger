from peewee import SqliteDatabase, Model
from peewee import ForeignKeyField, CharField, FloatField, BooleanField, DateTimeField, TextField


class BaseModel(Model):
    """A base model that will use our Sqlite database."""
    class Meta:
        database = None


class Watch(BaseModel):
    name = CharField(primary_key=True)
    exception_raised = BooleanField()
    last_run = DateTimeField(null=True)


class File(BaseModel):
    watch = ForeignKeyField(Watch)
    filename = CharField(max_length=640)
    last_modified = FloatField()


class Var(BaseModel):
    watch = ForeignKeyField(Watch)
    name = CharField(max_length=256)
    value = TextField()


def use_sqlite_db(sqlite_filename):
    db = SqliteDatabase(sqlite_filename)

    BaseModel._meta.database = db
    File._meta.database = db
    Watch._meta.database = db
    Var._meta.database = db

    if not Watch.table_exists():
        Watch.create_table()
    if not File.table_exists():
        File.create_table()
    if not Var.table_exists():
        Var.create_table()
