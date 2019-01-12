print()

import configparser
from ConversationsSqliteDb import ConversationsSqliteDb
import socket
from datetime import datetime
import json
import tweepy
from PicturesSqliteDb import PicturesSqliteDb
from pymongo import MongoClient
import signal
import sys
import time
from common_twitter import get_tweet_url

################################################################################
#
# CONF
#
################################################################################

#
# Secret
#

secret_config = configparser.ConfigParser()
secret_config.read('segreto.conf')
consumer_key = secret_config.get('Twitter', 'consumer_key')
consumer_secret = secret_config.get('Twitter', 'consumer_secret')
access_key = secret_config.get('Twitter', 'access_key')
access_secret = secret_config.get('Twitter', 'access_secret')

#
# Data
#

config = configparser.ConfigParser()
config.read('toast.conf')

# Pictures
pictures_database_path = config.get('Pictures', 'database')
pictures_db = PicturesSqliteDb(pictures_database_path)
picture_symbol = config.get('Pictures', 'symbol')

# Conversations
conversation_database_path = config.get(
    'Conversations', 'database')
conversations_db = ConversationsSqliteDb(conversation_database_path)
conversation_symbol = config.get('Conversations', 'symbol')

# MongoDB
database_name = config.get('Tweets', 'database')
collection_name = config.get('Tweets', 'collection')
client = MongoClient()
db = client[database_name]
collection = db[collection_name]

# Streaming
track = config.get('Streaming', 'track').split(",")
track = list(map(str.strip, track))
streaming_symbol = config.get('Streaming', 'symbol')
retweet_symbol = config.get('Streaming', 'retweet_symbol')
quoted_tweet_symbol = config.get('Streaming', 'quoted_tweet_symbol')

################################################################################
#
# GO
#
################################################################################

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True,
                 wait_on_rate_limit_notify=True, compression=True)


class StreamListener(tweepy.StreamListener):

    def on_status(self, status):
        raw_json = status._json
        date = datetime.fromtimestamp(float(status.timestamp_ms) / 1000)

        o = {"raw": raw_json}
        id = collection.insert_one(o).inserted_id

        # Pictures
        number_of_pictures = 0
        if "media" in status.entities:
            for e in status.entities["media"]:
                number_of_pictures += 1
                pictures_db.census_picture_tweet(status.id_str, e["media_url"])

        in_reply_to = status.in_reply_to_status_id_str

        # Retweet
        rt = hasattr(status, "retweeted_status")
        if rt:
            if status.retweeted_status.in_reply_to_status_id_str:
                in_reply_to = status.retweeted_status.in_reply_to_status_id_str

        # Conversation
        conversations_db.census_tweet(status.id_str, in_reply_to)

        # Quoted tweet
        # TODO
        quoted_tweet = hasattr(status, "quoted_status")

        print(
            f"{streaming_symbol}  🐦 {get_tweet_url(status.id_str)} 🕓 {date} 💾 {id} {retweet_symbol if rt else ''}{picture_symbol * number_of_pictures}{conversation_symbol if in_reply_to else ''}{quoted_tweet_symbol if quoted_tweet else ''}"
        )

    def on_error(self, status_code):
        print(f'{streaming_symbol}  ERROR: {status_code}')
        if status_code == 420:
            # returning False in on_data disconnects the stream
            return False


stream_listener = StreamListener()
stream = tweepy.Stream(auth=api.auth, listener=stream_listener)


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    client.close()
    stream.disconnect()
    print('Ciao!')


signal.signal(signal.SIGINT, signal_handler)
stream.filter(track=track)
