import configparser
import hashlib
import os
from pathlib import Path
import requests
import sys
import urllib.request

from common_twitter import get_tweet_url
from PicturesSqliteDb import PicturesSqliteDb

config = configparser.ConfigParser()
config.read('toast.conf')
pictures_database_path = config.get('Pictures', 'database')
pictures_db = PicturesSqliteDb(pictures_database_path)
pictures_download_directory = Path(
    config.get('Pictures', 'directory'))
symbol = config.get('Pictures', 'symbol')

if not os.path.exists(pictures_download_directory):
    os.makedirs(pictures_download_directory)


def init(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_file_extension(type, url):
    if type == 'p':
        return Path(url.split('/')[-1]).suffix
    elif type == 'v':
        p = url.split('/')[-1]
        p = p.split('?')[0]
        return Path(p).suffix
    else:
        return None


def download_picture(tweet_id, type, url):
    try:
        response = requests.get(url, timeout=5)
        sha1 = hashlib.sha1()
        sha1.update(response.content)
        sha1 = sha1.hexdigest()
        extension = get_file_extension(type, url)
        filename = sha1 + extension
        with open(pictures_download_directory / filename, 'wb') as fout:
            fout.write(response.content)
        print(f"{symbol}  {tweet_id} {url} -> {filename}")
        return (sha1, extension)
    except requests.exceptions.RequestException as e:
        print(e)
        return (None, None)


def process_queue():
    pictures = pictures_db.get_all_no_sha1()
    for picture in pictures:
        print(
            f"{symbol}  Trying to download {picture['url']} (from tweet {get_tweet_url(picture['tweet_id'])})…")
        (sha1, extension) = download_picture(
            picture["tweet_id"],
            picture["type"],
            picture["url"],
        )
        if sha1 and extension:
            pictures_db.set_sha1(
                extension.replace(".", ""),
                sha1,
                picture["tweet_id"],
                picture["url"]
            )
        else:
            print(f"{symbol}  error")
            pictures_db.census_error(
                picture["media_id"], picture["tweet_id"], picture["url"])
