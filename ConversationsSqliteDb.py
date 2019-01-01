from datetime import datetime

from CommonSqliteAbstractDb import CommonSqliteAbstractDb


class ConversationsSqliteDb(CommonSqliteAbstractDb):
    def __init__(self, path):
        super().__init__(path)
        cursor = self.db.cursor()
        cursor.execute("""
            -- W by collazionare.py process | R by conversations_service.py process
            CREATE TABLE IF NOT EXISTS collected_tweets (
                tweet_id TEXT,
                in_reply_to_status_id TEXT,
                PRIMARY KEY (tweet_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS root_tweets (
                tweet_id TEXT,
                root_tweet_id TEXT,
                PRIMARY KEY (tweet_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraped_tweets (
                tweet_id TEXT,
                last_check TEXT,
                PRIMARY KEY (tweet_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                root_tweet_id TEXT,
                tweet_id TEXT,
                conversation_id TEXT,
                tweet_timestamp TEXT,
                tweet_text TEXT,
                user_id TEXT,
                user_name TEXT,
                user_screenname TEXT,
                PRIMARY KEY (root_tweet_id, tweet_id)
            )
        """)
        self.db.commit()

    def census_tweet(self, tweet_id, in_reply_to_status_id):
        c = self.db.cursor()
        if not c.execute(
            'SELECT * FROM collected_tweets WHERE tweet_id = ?',
            (tweet_id,)
        ).fetchone():
            c.execute(
                'INSERT INTO collected_tweets (tweet_id, in_reply_to_status_id) VALUES (?, ?)',
                (tweet_id, in_reply_to_status_id)
            )
        self.db.commit()

    def get_root_tweet_id(self, tweet_id):
        c = self.db.cursor()
        return c.execute(
            'SELECT * FROM root_tweets WHERE tweet_id = ?',
            (tweet_id)
        ).fetchone()

    def get_tweet_id_with_no_root_tweet(self):
        c = self.db.cursor()
        return c.execute(
            """
            SELECT ct.tweet_id
            FROM collected_tweets ct
            LEFT JOIN root_tweets rt
            ON ct.tweet_id = rt.tweet_id
            WHERE rt.tweet_id IS NULL 
            """
        ).fetchall()

    def set_root_tweet_id(self, tweet_id, root_tweet_id):
        c = self.db.cursor()
        if not c.execute('SELECT * FROM root_tweets WHERE tweet_id = ?', (tweet_id,)).fetchone():
            c.execute(
                'INSERT INTO root_tweets (tweet_id, root_tweet_id) VALUES (?, ?)',
                (tweet_id, root_tweet_id)
            )
        self.db.commit()

    def update_scraping_last_check(self, tweet_id, now):
        c = self.db.cursor()
        c.execute(
            'UPDATE scraped_tweets SET last_check = ? WHERE tweet_id = ?',
            (now, tweet_id)
        )

    def add_tweet_in_conversation(self, root_tweet_id, tweet_id, conversation_id, tweet_timestamp, tweet_text, user_id, user_name, user_screenname):
        c = self.db.cursor()
        if not c.execute('SELECT * FROM conversations WHERE root_tweet_id = ? AND tweet_id = ?',
                         (root_tweet_id, tweet_id)).fetchone():
            c.execute(
                """INSERT INTO conversations (
                    root_tweet_id,
                    tweet_id,
                    conversation_id,
                    tweet_timestamp,
                    tweet_text,
                    user_id,
                    user_name,
                    user_screenname
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (root_tweet_id, tweet_id, conversation_id, tweet_timestamp, tweet_text, user_id, user_name, user_screenname)
            )
            self.db.commit()
