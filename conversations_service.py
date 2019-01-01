import configparser
import json
import requests
import socket

from common_twitter import get_tweet_url
from conversations_scraping import process_queue_get_root_tweets
from ConversationsSqliteDb import ConversationsSqliteDb

#
# CONF
#

collazionare_config = configparser.ConfigParser()
collazionare_config.read('toast.conf')
conversations_database_path = collazionare_config.get(
    'Conversations', 'database')
conversations_db = ConversationsSqliteDb(conversations_database_path)
port = int(collazionare_config.get('Conversations', 'service_port'))
symbol = collazionare_config.get('Conversations', 'symbol')

#
# LISTEN
#

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('127.0.0.1', port))
    s.listen()
    conn, addr = s.accept()
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"{symbol}  ping!")
            process_queue_get_root_tweets()
