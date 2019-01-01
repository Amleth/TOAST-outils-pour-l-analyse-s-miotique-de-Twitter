print()

import configparser
from ConversationsSqliteDb import ConversationsSqliteDb
import socket
from datetime import datetime
import json
import tweepy
from PicturesSqliteDb import PicturesSqliteDb
from pymongo import MongoClient
import time

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

collazionare_config = configparser.ConfigParser()
collazionare_config.read('toast.conf')

# Pictures
pictures_database_path = collazionare_config.get('Pictures', 'database')
pictures_db = PicturesSqliteDb(pictures_database_path)
pictures_service_port = int(
    collazionare_config.get('Pictures', 'service_port'))
picture_symbol = collazionare_config.get('Pictures', 'symbol')

# Conversations
conversation_database_path = collazionare_config.get(
    'Conversations', 'database')
conversations_db = ConversationsSqliteDb(conversation_database_path)
conversations_service_port = int(
    collazionare_config.get('Conversations', 'service_port'))
conversation_symbol = collazionare_config.get('Conversations', 'symbol')

# MongoDB
database_name = collazionare_config.get('Tweets', 'database')
collection_name = collazionare_config.get('Tweets', 'collection')
client = MongoClient()
db = client[database_name]
collection = db[collection_name]

# Streaming
track = collazionare_config.get('Streaming', 'track').split(",")
track = list(map(str.strip, track))
streaming_symbol = collazionare_config.get('Streaming', 'symbol')

################################################################################
#
# GO
#
################################################################################

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True,
                 wait_on_rate_limit_notify=True, compression=True)

# Pictures service

try:
    pictures_service_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pictures_service_socket.connect(('127.0.0.1', pictures_service_port))
except ConnectionRefusedError as e:
    pictures_service_socket = None
    print(
        f"{streaming_symbol}  Can't connect to pictures service on port {pictures_service_port} —", e)

# Conversations service

try:
    conversations_service_socket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    conversations_service_socket.connect(
        ('127.0.0.1', conversations_service_port))
except ConnectionRefusedError as e:
    conversations_service_socket = None
    print(
        f"{streaming_symbol}  Can't connect to conversations service on port {conversations_service_port} —", e)


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
                if pictures_service_socket:
                    pictures_service_socket.sendall(b"ping")

        # Conversation
        conversations_db.census_tweet(
            status.id_str, status.in_reply_to_status_id_str)
        if status.in_reply_to_status_id_str:
            if conversations_service_socket:
                conversations_service_socket.sendall(b"ping")

        print(
            f"{streaming_symbol}  🐦 {status.id_str} 🕓 {date} 💾 {id} {picture_symbol * number_of_pictures}{conversation_symbol if status.in_reply_to_status_id_str else ''}"
        )

    def on_error(self, status_code):
        print(f'{streaming_symbol}  ERROR: {status_code}')
        if status_code == 420:
            # returning False in on_data disconnects the stream
            return False


stream_listener = StreamListener()
stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
stream.filter(track=track)
