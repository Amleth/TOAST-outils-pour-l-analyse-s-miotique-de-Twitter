print()

import configparser
# from ConversationsSqliteDb import ConversationsSqliteDb
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
from ssl import SSLError
from requests.exceptions import Timeout, ConnectionError
from urllib3.exceptions import ReadTimeoutError

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
video_symbol = config.get('Pictures', 'symbol_video')

# Conversations
conversation_database_path = config.get(
    'Conversations', 'database')
# conversations_db = ConversationsSqliteDb(conversation_database_path)
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

        o = {
            "raw": raw_json,
            "fulltext": fulltext,
            "track": config.get('Streaming', 'track')
        }
        id = collection.insert_one(o).inserted_id

        # Pictures
        number_of_pictures = 0
        number_of_videos = 0
        media = None
        if not rt:
            if not hasattr(status, "extended_tweet"):
                # Tweet non retweeté < 140 caractères
                # type = "NORT_NOET"
                if "media" in status.entities:
                    media = status.entities['media']
            else:
                # Tweet non retweeté > 140 caractères
                # type = "NORT_ET"
                if "media" in status.extended_tweet["entities"]:
                    media = status.extended_tweet["entities"]["media"]
        else:
            if not hasattr(status.retweeted_status, "extended_tweet"):
                # Tweet retweeté < 140 caractères
                # type = "RT_NOET"
                if "media" in status.retweeted_status.entities:
                    media = status.retweeted_status.entities["media"]
            else:
                # Tweet retweeté > 140 caractères
                # type = "RT_ET"
                if "media" in status.retweeted_status.extended_tweet["entities"]:
                    media = status.retweeted_status.extended_tweet["entities"]['media']
        if media:
            for m in media:
                if "video_info" in m:
                    number_of_videos += 1
                    for v in m["video_info"]["variants"]:
                        if "bitrate" in v:
                            if int(v["bitrate"]) == 2176000:
                                pictures_db.census_picture_tweet(
                                    status.id_str,
                                    "v",
                                    v["url"]
                                )
                else:
                    number_of_pictures += 1
                    pictures_db.census_picture_tweet(
                        status.id_str,
                        "p",
                        m["media_url"]
                    )

        in_reply_to = status.in_reply_to_status_id_str
        if rt:
            if status.retweeted_status.in_reply_to_status_id_str:
                in_reply_to = status.retweeted_status.in_reply_to_status_id_str

        # Conversation
        # conversations_db.census_tweet(status.id_str, in_reply_to)
        # TODO

        # Quoted tweet
        quoted_tweet = hasattr(status, "quoted_status")
        # TODO

        print("================================================================================")
        print(
            f"{streaming_symbol}  🐦 {get_tweet_url(status.id_str)} 🕓 {date} 💾 {id} {retweet_symbol if rt else ''}{picture_symbol * number_of_pictures}{video_symbol * number_of_videos}{conversation_symbol if in_reply_to else ''}{quoted_tweet_symbol if quoted_tweet else ''}"
        )
        print(f"{fulltext}")

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
stream.filter(track=track)  # , is_async=True
