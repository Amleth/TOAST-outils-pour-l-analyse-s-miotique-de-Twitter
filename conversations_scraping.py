from bs4 import BeautifulSoup
import configparser
from datetime import datetime
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

from common_twitter import get_tweet_url
from ConversationsSqliteDb import ConversationsSqliteDb

collazionare_config = configparser.ConfigParser()
collazionare_config.read('toast.conf')
conversation_symbol = collazionare_config.get('Conversations', 'symbol')
geckodriver_path = collazionare_config.get('Conversations', 'geckodriver_path')
conversation_database_path = collazionare_config.get(
    'Conversations', 'database')
symbol = collazionare_config.get('Conversations', 'symbol')
conversations_db = ConversationsSqliteDb(conversation_database_path)


def process_queue_get_root_tweets():
    for t in conversations_db.get_tweet_id_with_no_root_tweet():
        root_tweet_id = get_root_tweet(t["tweet_id"])
        if root_tweet_id:
            conversations_db.set_root_tweet_id(t["tweet_id"], root_tweet_id)


def get_root_tweet(tweet_id):
    page = requests.get(get_tweet_url(tweet_id))
    soup = BeautifulSoup(page.content, features="lxml")
    root_tweet_id = soup.find(
        "li", {"data-item-id": re.compile(r".*")}
    )['data-item-id']

    print(f"{symbol}  Root tweet found: {get_tweet_url(tweet_id)} -> {get_tweet_url(root_tweet_id)}")

    return root_tweet_id


# def scrape(tweet_id):
#     #
#     # AJAX REQUESTS TRIGGERED BY MOUSE GESTURES (SCROLLING & CLICKS) AUTOMATISATION
#     #

#     browser = webdriver.Firefox(executable_path=geckodriver_path)
#     browser.get(get_tweet_url(tweet_id))
#     page = browser.find_element_by_tag_name('body')
#     browser.close()

#     while not browser.find_element_by_css_selector('div.stream-end-inner').is_displayed():
#         page.send_keys(Keys.PAGE_DOWN)
#         time.sleep(0.5)
#         print(f'{conversation_symbol}  page down…')

#     more_replies_links = browser.find_elements_by_class_name(
#         'ThreadedConversation-moreRepliesLink')
#     for x in range(0, len(more_replies_links)):
#         if more_replies_links[x].is_displayed():
#             more_replies_links[x].click()

#     #
#     # TWEETS SELECTION
#     #

#     selector = Selector(text=browser.page_source)

#     # Root tweet

#     root_user_screenname = selector.css(
#         'div.permalink-inner.permalink-tweet-container > div.tweet.permalink-tweet ::attr(data-screen-name)').extract_first()
#     root_user_name = selector.css(
#         'div.permalink-inner.permalink-tweet-container > div.tweet.permalink-tweet ::attr(data-name)').extract_first()
#     root_user_userid = selector.css(
#         'div.permalink-inner.permalink-tweet-container > div.tweet.permalink-tweet ::attr(data-user-id)').extract_first()
#     root_text = selector.css('div.permalink-inner.permalink-tweet-container').css(
#         '.TweetTextSize ::text').extract_first()
#     root_timestamp = selector.css(
#         '.permalink-header').css('.time').css('span ::attr(data-time)').extract_first()

#     # print(root_user_screenname, root_user_name,
#     #       root_user_screenname, root_timestamp, root_text)

#     # Conversations

#     count = 0
#     conversations_count = 0
#     lone_tweets_count = 0

#     for conversation in selector.css('.ThreadedConversation'):
#         conversations_count += 1
#         for tweet in conversation.css('.ThreadedConversation-tweet'):
#             count += 1
#             tweet_id = tweet.css(
#                 'div.tweet ::attr(data-tweet-id)').extract_first()
#             tweet_user_screenname = tweet.css(
#                 'div.tweet ::attr(data-screen-name)').extract_first()
#             tweet_user_name = tweet.css(
#                 'div.tweet ::attr(data-name)').extract_first()
#             tweet_user_id = tweet.css(
#                 'div.tweet ::attr(data-user-id)').extract_first()
#             tweet_text = tweet.css('.TweetTextSize ::text').extract()
#             tweet_text = ''.join(tweet_text)
#             tweet_text = tweet_text.replace('\n', '')
#             tweet_timestamp = tweet.css(
#                 'span._timestamp ::attr(data-time)').extract_first()
#             print(tweet_id, tweet_user_screenname,
#                   tweet_user_name, tweet_user_id, tweet_timestamp)
#             print(tweet_text)

#     for tweet in selector.css('.ThreadedConversation--loneTweet'):
#         count += 1
#         lone_tweets_count += 1
#         tweet_id = tweet.css('div.tweet ::attr(data-tweet-id)').extract_first()
#         tweet_user_screenname = tweet.css(
#             'div.tweet ::attr(data-screen-name)').extract_first()
#         tweet_user_name = tweet.css(
#             'div.tweet ::attr(data-name)').extract_first()
#         tweet_user_id = tweet.css(
#             'div.tweet ::attr(data-user-id)').extract_first()
#         tweet_text = tweet.css('.TweetTextSize ::text').extract()
#         tweet_text = ''.join(tweet_text)
#         tweet_text = tweet_text.replace('\n', '')
#         tweet_timestamp = tweet.css(
#             'span._timestamp ::attr(data-time)').extract_first()
#         # print(tweet_id, tweet_user_screenname,
#         #       tweet_user_name, tweet_user_id, tweet_timestamp, tweet_text)

#     browser.close()

#     print(f'{conversation_symbol}  {count} {conversations_count} {lone_tweets_count}')
