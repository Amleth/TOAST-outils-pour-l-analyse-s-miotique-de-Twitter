import json
import pprint
from pymongo import MongoClient
import xlsxwriter

workbook = xlsxwriter.Workbook("data.xlsx")
worksheet = workbook.add_worksheet()

bold = workbook.add_format({"bold": True})
worksheet.write(0, 0, "created_at", bold)
worksheet.write(0, 1, "id_str", bold)
worksheet.write(0, 2, "retweeted_status_created_at", bold)
worksheet.write(0, 3, "retweeted_status_id_str", bold)
worksheet.write(0, 4, "source", bold)
worksheet.write(0, 5, "text", bold)
worksheet.write(0, 6, "timestamp_ms", bold)
worksheet.write(0, 7, "user_id_str", bold)
worksheet.write(0, 8, "user_name", bold)
worksheet.write(0, 9, "user_screen_name", bold)
worksheet.write(0, 10, "user_description", bold)

client = MongoClient()
db = client.si90
collection = db.si90

line = 1

for t in collection.find():
    # READ

    j = t["raw"]

    created_at = j["created_at"]

    id_str = j["id_str"]

    retweeted_status_created_at = None
    retweeted_status_id_str = None
    in_reply_to_status_id_str = j["in_reply_to_status_id_str"]
    if "retweeted_status" in j:
        retweeted_status_created_at = j["retweeted_status"]["created_at"]
        retweeted_status_id_str = j["retweeted_status"]["id_str"]

    source = j["source"]

    text = None

    if "retweeted_status" in j:
        if not 'extended_tweet' in j['retweeted_status']:
            text = j['retweeted_status']['text']
        else:
            text = j['retweeted_status']['extended_tweet']['full_text']
    else:
        if not 'extended_tweet' in j:
            text = j['text']
        else:
            text = j['extended_tweet']['full_text']

    timestamp_ms = j["timestamp_ms"]

    user_id_str = j["user"]["id_str"]
    user_name = j["user"]["name"]
    user_screen_name = j["user"]["screen_name"]
    user_description = j["user"]["description"]

    # WRITE
    worksheet.write(line, 0, created_at)
    worksheet.write(line, 1, id_str)
    worksheet.write(line, 2, retweeted_status_created_at)
    worksheet.write(line, 3, retweeted_status_id_str)
    worksheet.write(line, 4, source)
    worksheet.write(line, 5, text)
    worksheet.write(line, 6, timestamp_ms)
    worksheet.write(line, 7, user_id_str)
    worksheet.write(line, 8, user_name)
    worksheet.write(line, 9, user_screen_name)
    worksheet.write(line, 10, user_description)

    line += 1

workbook.close()
