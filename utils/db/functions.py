from django.db.models import Func


class StrPos(Func):
    function = 'POSITION'   # MySQL method

    def as_sqlite(self, compiler, connection):
        #  SQLite method
        return self.as_sql(compiler, connection, function='INSTR')

    def as_postgresql(self, compiler, connection):
        # PostgreSQL method
        return self.as_sql(compiler, connection, function='STRPOS')
