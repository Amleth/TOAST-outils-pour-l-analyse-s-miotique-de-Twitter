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
worksheet.write(0, 7, "urls", bold)
worksheet.write(0, 8, "user_id_str", bold)
worksheet.write(0, 9, "user_name", bold)
worksheet.write(0, 10, "user_screen_name", bold)

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

    text = j["text"]

    timestamp_ms = j["timestamp_ms"]

    urls = []
    for url in j["entities"]["urls"]:
        urls.append({"url": url["url"], "expanded_url": url["expanded_url"]})
    urls = json.dumps(urls)

    user_id_str = j["user"]["id_str"]
    user_name = j["user"]["name"]
    user_screen_name = j["user"]["screen_name"]

    # WRITE
    worksheet.write(line, 0, created_at)
    worksheet.write(line, 1, id_str)
    worksheet.write(line, 2, retweeted_status_created_at)
    worksheet.write(line, 3, retweeted_status_id_str)
    worksheet.write(line, 4, source)
    worksheet.write(line, 5, text)
    worksheet.write(line, 6, timestamp_ms)
    worksheet.write(line, 7, urls)
    worksheet.write(line, 8, user_id_str)
    worksheet.write(line, 9, user_name)
    worksheet.write(line, 10, user_screen_name)

    line += 1

workbook.close()
