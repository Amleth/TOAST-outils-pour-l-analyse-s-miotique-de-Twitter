from bs4 import BeautifulSoup
from colorama import Back, Fore, Style
import configparser
from datetime import datetime
import re
import requests
from scrapy.selector import Selector
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

from common_twitter import get_tweet_url
from ConversationsSqliteDb import ConversationsSqliteDb

config = configparser.ConfigParser()
config.read('toast.conf')
symbol = config.get('Conversations', 'symbol')
geckodriver_path = config.get('Conversations', 'geckodriver_path')
conversation_database_path = config.get(
    'Conversations', 'database')
conversations_db = ConversationsSqliteDb(conversation_database_path)

TEXT_GETTING_URL = 'getting url'
TEXT_ROOT_TWEET_SCRAPED = 'root tweet scraped'
TEXT_NO_ROOT_TWEET = 'no root tweet'


def process_queue_get_root_tweets():
    for t in conversations_db.get_tweet_id_with_no_root_tweet():
        print(
            f"{symbol}  {TEXT_GETTING_URL.ljust(20)}{t['tweet_id']} — {get_tweet_url(t['tweet_id'])}")
        root_tweet_id = get_root_tweet(t["tweet_id"])
        if root_tweet_id:
            print(
                f"{Style.DIM}{symbol}  {TEXT_ROOT_TWEET_SCRAPED.ljust(20)}{root_tweet_id} — {get_tweet_url(root_tweet_id)}{Style.RESET_ALL}"
            )
        else:
            print(
                f"{Style.DIM}{symbol}  {TEXT_NO_ROOT_TWEET}{Style.RESET_ALL}"
            )
        conversations_db.set_root_tweet_id(t["tweet_id"], root_tweet_id)


def process_queue_scrape_root_tweets():
    count = 0
    for t in conversations_db.get_unscraped_root_tweets():
        count += 1
        print(
            f"{symbol}  {'scraping'.ljust(20)}{get_tweet_url(t['tweet_id'])}"
        )
        scrape(t['tweet_id'])


def get_root_tweet(tweet_id):
    try:
        response = requests.get(get_tweet_url(tweet_id))
        redirected_tweet_id = response.url.split('/')[-1]  # if retweet
        print(
            f"{Style.DIM}{symbol}  {'response.url'.ljust(20)}{redirected_tweet_id} — {response.url}")
        selector = Selector(text=response.content)
        root_tweet_id = selector.css(
            'div.permalink-inner div.tweet ::attr(data-item-id)').extract_first()
        if root_tweet_id == redirected_tweet_id:
            return False
        else:
            return root_tweet_id
    except:
        return root_tweet_id


def scrape(root_tweet_id):
    #
    # AJAX REQUESTS TRIGGERED BY MOUSE GESTURES (SCROLLING & CLICKS) AUTOMATISATION
    #

    browser = webdriver.Firefox(executable_path=geckodriver_path)
    browser.get(get_tweet_url(root_tweet_id))
    page = browser.find_element_by_tag_name('body')

    try:
        if not browser.find_element_by_css_selector('div.permalink-footer').is_displayed():
            while not browser.find_element_by_css_selector('div.stream-end-inner').is_displayed():
                page.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.5)
                print(f'{symbol}  page down…')

        more_replies_links = browser.find_elements_by_class_name(
            'ThreadedConversation-moreRepliesLink')
        for x in range(0, len(more_replies_links)):
            if more_replies_links[x].is_displayed():
                more_replies_links[x].click()

        #
        # TWEETS SELECTION
        #

        selector = Selector(text=browser.page_source)

        # Root tweet

        root_user_screenname = selector.css(
            'div.permalink-inner.permalink-tweet-container > div.tweet.permalink-tweet ::attr(data-screen-name)').extract_first()
        root_user_name = selector.css(
            'div.permalink-inner.permalink-tweet-container > div.tweet.permalink-tweet ::attr(data-name)').extract_first()
        root_user_userid = selector.css(
            'div.permalink-inner.permalink-tweet-container > div.tweet.permalink-tweet ::attr(data-user-id)').extract_first()
        root_text = selector.css('div.permalink-inner.permalink-tweet-container').css(
            '.TweetTextSize ::text').extract_first()
        root_timestamp = selector.css(
            '.permalink-header').css('.time').css('span ::attr(data-time)').extract_first()

        conversations_db.add_tweet_in_conversation(
            root_tweet_id,
            root_tweet_id,
            0,
            root_timestamp,
            root_text,
            root_user_userid,
            root_user_name,
            root_user_screenname
        )

        # Conversations

        count = 0
        conversations_count = 0
        lone_tweets_count = 0

        for conversation in selector.css('.ThreadedConversation'):
            conversations_count += 1
            for tweet in conversation.css('.ThreadedConversation-tweet'):
                count += 1
                tweet_id = tweet.css(
                    'div.tweet ::attr(data-tweet-id)').extract_first()
                tweet_user_screenname = tweet.css(
                    'div.tweet ::attr(data-screen-name)').extract_first()
                tweet_user_name = tweet.css(
                    'div.tweet ::attr(data-name)').extract_first()
                tweet_user_id = tweet.css(
                    'div.tweet ::attr(data-user-id)').extract_first()
                tweet_text = tweet.css('.TweetTextSize ::text').extract()
                tweet_text = ''.join(tweet_text)
                tweet_text = tweet_text.replace('\n', '')
                tweet_timestamp = tweet.css(
                    'span._timestamp ::attr(data-time)').extract_first()
                conversations_db.add_tweet_in_conversation(
                    root_tweet_id,
                    tweet_id,
                    conversations_count,
                    tweet_timestamp,
                    tweet_text,
                    tweet_user_id,
                    tweet_user_name,
                    tweet_user_screenname
                )

        for tweet in selector.css('.ThreadedConversation--loneTweet'):
            count += 1
            lone_tweets_count += 1
            tweet_id = tweet.css(
                'div.tweet ::attr(data-tweet-id)').extract_first()
            tweet_user_screenname = tweet.css(
                'div.tweet ::attr(data-screen-name)').extract_first()
            tweet_user_name = tweet.css(
                'div.tweet ::attr(data-name)').extract_first()
            tweet_user_id = tweet.css(
                'div.tweet ::attr(data-user-id)').extract_first()
            tweet_text = tweet.css('.TweetTextSize ::text').extract()
            tweet_text = ''.join(tweet_text)
            tweet_text = tweet_text.replace('\n', '')
            tweet_timestamp = tweet.css(
                'span._timestamp ::attr(data-time)').extract_first()

            conversations_db.add_tweet_in_conversation(
                root_tweet_id,
                tweet_id,
                conversations_count,
                tweet_timestamp,
                tweet_text,
                tweet_user_id,
                tweet_user_name,
                tweet_user_screenname
            )

        browser.close()

        print(f'{symbol}  {count}t {conversations_count}c {lone_tweets_count}l')

    except Exception as e:
        print(f'{symbol}  {e}')
        browser.close()
