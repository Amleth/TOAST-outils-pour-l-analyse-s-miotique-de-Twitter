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
from urllib3.exceptions import ProtocolError

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

        # Is retweet?
        rt = hasattr(status, "retweeted_status")

        # Extraction du texte complet
        fulltext = None
        if not rt:
            fulltext = status.text
            if hasattr(status, "extended_tweet"):
                fulltext = status.extended_tweet['full_text']
        else:
            fulltext = status.retweeted_status.text
            if hasattr(status.retweeted_status, "extended_tweet"):
                fulltext = status.retweeted_status.extended_tweet['full_text']

        # Écriture du tweet dans MongoDB

        o = {"raw": raw_json, "fulltext": fulltext}
        id = collection.insert_one(o).inserted_id

        # TODO
        # Pictures
        number_of_pictures = 0
        pictures_urls = []
        videos_urls = []
        # media = None
        # if not rt:
        #     if not hasattr(status, "extended_tweet"):
        #         # Tweet non retweeté < 140 caractères
        #         if hasattr(status, "entities"):
        #             if hasattr(status.entities, "media"):
        #                 media = status.entities.media
        #                 print(1)
        #     else:
        #         # Tweet non retweeté > 140 caractères
        #         if hasattr(status.extended_tweet, "entities"):
        #             if hasattr(status.extended_tweet.entities, "media"):
        #                 media = status.extended_tweet.entities.media
        #                 print(2)
        # else:
        #     if not hasattr(status.retweeted_status, "extended_tweet"):
        #         print(status.retweeted_status)
        #         # Tweet retweeté < 140 caractères
        #         if hasattr(status.retweeted_status, "entities"):
        #             if hasattr(status.retweeted_status.entities, "media"):
        #                 media = status.retweeted_status.entities.media
        #                 print(3)
        #     else:
        #         # Tweet retweeté > 140 caractères
        #         if hasattr(status.retweeted_status.extended_tweet, "entities"):
        #             if hasattr(status.retweeted_status.extended_tweet.entities, "media"):
        #                 media = status.retweeted_status.extended_tweet.entities.media
        #                 print(4)
        # print(media)
        # if "media" in status.entities:
        #     for e in media:
        #         number_of_pictures += 1
        #         pictures_db.census_picture_tweet(status.id_str, e["media_url"])

        in_reply_to = status.in_reply_to_status_id_str
        if rt:
            if status.retweeted_status.in_reply_to_status_id_str:
                in_reply_to = status.retweeted_status.in_reply_to_status_id_str

        # Conversation
        conversations_db.census_tweet(status.id_str, in_reply_to)

        # Quoted tweet
        quoted_tweet = hasattr(status, "quoted_status")
        # TODO

        print("================================================================================")
        print(
            f"{streaming_symbol}  🐦 {get_tweet_url(status.id_str)} 🕓 {date} 💾 {id} {retweet_symbol if rt else ''}{picture_symbol * number_of_pictures}{conversation_symbol if in_reply_to else ''}{quoted_tweet_symbol if quoted_tweet else ''}"
        )
        # print(f"{fulltext}")
        print(videos_urls)
        print(pictures_urls)

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

# while True:
#     try:
#         stream.filter(track=track)
#     except Exception as error:
#         print(error)
#         continue
