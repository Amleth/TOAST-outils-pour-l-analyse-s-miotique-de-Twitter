import configparser
import json
from pictures_common import process_queue
import socket
from PicturesSqliteDb import PicturesSqliteDb

#
# CONF
#

collazionare_config = configparser.ConfigParser()
collazionare_config.read('toast.conf')
pictures_database_path = collazionare_config.get('Pictures', 'database')
port = int(collazionare_config.get('Pictures', 'service_port'))
symbol = collazionare_config.get('Pictures', 'symbol')

pictures_db = PicturesSqliteDb(pictures_database_path)

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
            process_queue()
