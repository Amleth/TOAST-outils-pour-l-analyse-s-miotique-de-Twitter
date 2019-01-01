import hashlib
import configparser
import os
from pathlib import Path
import requests
import sys
import urllib.request
from PicturesSqliteDb import PicturesSqliteDb

collazionare_config = configparser.ConfigParser()
collazionare_config.read('toast.conf')
pictures_database_path = collazionare_config.get('Pictures', 'database')
pictures_db = PicturesSqliteDb(pictures_database_path)
pictures_download_directory = Path(
    collazionare_config.get('Pictures', 'directory'))
symbol = collazionare_config.get('Pictures', 'symbol')

if not os.path.exists(pictures_download_directory):
    os.makedirs(pictures_download_directory)


def init(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_file_extension(url):
    return Path(url.split('/')[-1]).suffix


def download_picture(tweet_id, url):
    response = requests.get(url)
    sha1 = hashlib.sha1()
    sha1.update(response.content)
    sha1 = sha1.hexdigest()
    extension = get_file_extension(url)
    filename = sha1 + get_file_extension(url)
    with open(pictures_download_directory / filename, 'wb') as fout:
        fout.write(response.content)
    print(f"{symbol}  {tweet_id} {url} -> {filename}")
    return (sha1, extension)


def process_queue():
    pictures = pictures_db.get_all_no_sha1()
    for picture in pictures:
        (sha1, extension) = download_picture(
            picture["tweet_id"],
            picture["url"]
        )
        pictures_db.set_sha1(
            extension.replace(".", ""),
            sha1,
            picture["tweet_id"],
            picture["url"]
        )
