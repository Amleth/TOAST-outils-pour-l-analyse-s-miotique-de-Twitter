from CommonSqliteAbstractDb import CommonSqliteAbstractDb


class PicturesSqliteDb(CommonSqliteAbstractDb):
    def __init__(self, path):
        super().__init__(path)
        cursor = self.db.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pictures (
            error INTEGER,
            extension TEXT,
            sha1 TEXT,
            tweet_id TEXT,
            type TEXT,
            url TEXT,
            PRIMARY KEY (url, tweet_id),
            UNIQUE (url, sha1, tweet_id)
        )
        """)
        self.db.commit()

    def census_picture_tweet(self, tweet_id, type, url):
        c = self.db.cursor()
        exists = self.get(url, tweet_id)
        if not exists:
            c.execute(
                'INSERT INTO pictures (error, url, tweet_id, type) VALUES (?, ?, ?, ?)',
                (-1, url, tweet_id, type)
            )
            self.db.commit()

    def get(self, tweet_id, url):
        c = self.db.cursor()
        return c.execute(
            'SELECT * FROM pictures WHERE tweet_id = ? AND url = ?',
            (tweet_id, url)
        ).fetchone()

    def census_error(self, tweet_id, type, url):
        self.census_picture_tweet(url, tweet_id, type)
        c = self.db.cursor()
        c.execute(
            'UPDATE pictures SET error = 1 WHERE tweet_id = ? AND url = ?',
            (tweet_id, url)
        )

    def set_sha1(self, extension, sha1, tweet_id, url):
        c = self.db.cursor()
        c.execute(
            'UPDATE pictures SET extension = ?, sha1 = ? WHERE tweet_id = ? AND url = ?',
            (extension, sha1, tweet_id, url)
        )
        self.db.commit()

    def get_all(self):
        c = self.db.cursor()
        c.execute("SELECT * FROM pictures")
        return c.fetchall()

    def get_all_no_sha1(self):
        c = self.db.cursor()
        c.execute("SELECT * FROM pictures WHERE error = -1 AND sha1 IS NULL")
        return c.fetchall()
