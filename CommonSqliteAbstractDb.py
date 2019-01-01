import sqlite3


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class CommonSqliteAbstractDb:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = dict_factory

    def attach(self, file, alias):
        cursor = self.db.cursor()
        cursor.execute(f"ATTACH {file} AS {alias}")
        self.db.commit()

    def close(self):
        self.db.close()

    def begin_transaction(self):
        cursor = self.db.cursor()
        cursor.execute('BEGIN')
        self.db.commit()

    def commit_transaction(self):
        cursor = self.db.cursor()
        cursor.execute('COMMIT')
        self.db.commit()

    def rollback_transaction(self):
        cursor = self.db.cursor()
        cursor.execute('ROLLBACK')
        self.db.commit()
