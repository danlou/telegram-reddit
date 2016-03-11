#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This is a Python based Telegram Bot for Reddit
# MIT License - Daniel Loureiro (danlou)

import sys
import logging
import dataset

import praw
import telegram

from config import *
from messages import *

# need to fix bugs before 1.0 release
__version__ = '0.9.1'

# initiate logger
logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format='%(asctime)s %(message)s')

logger = logging.getLogger(__name__)

# initiate reddit wrapper object
reddit = praw.Reddit(user_agent=RD_USERAGENT)

# connect to database
db = dataset.connect(DB_URL)


class RedditRobot():
    """
    Starts and maintains a connection to Telegram.
    Commands are processed by corresponding methods.
    
    Subreddits are specified through messages, which
    can come from users typing or pressing the buttons
    presented in Telegram's custom keyboard.
    
    Submissions that were already shown to a user are
    discarded and new submissions are recorded in a
    database before being shown.
    """

    def __init__(self):
        updater = telegram.Updater(token=TG_TOKEN)
        
        dp = updater.dispatcher
        dp.addTelegramCommandHandler('start', self.welcome)
        dp.addTelegramCommandHandler('suggest', self.suggest)
        dp.addTelegramCommandHandler('feedback', self.feedback)
        dp.addTelegramCommandHandler('stats', self.stats)
        dp.addTelegramMessageHandler(self.fetch)
        dp.addErrorHandler(self.error)
        
        updater.start_polling()

        logger.info("RedditRobot started polling")
        self.message = ''
        self.chat_id = None
        self.user_id = None
        self.subreddit = None
        self.submission = None

        #updater.idle()

    def welcome(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id, text=MSG_WELCOME)

    def suggest(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id, text=MSG_SUGGEST)

    def stats(self, bot, update):
        shown_count = len(db['shown'])
        users_count = len(list(db['shown'].distinct('userid')))
        stats_msg = '%d submissions delivered to %d users' % (shown_count, users_count)
        bot.sendMessage(chat_id=update.message.chat_id, text=stats_msg)
        logger.info("Presented stats")

    def feedback(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=MSG_RATE+TG_BOTNAME,
                        disable_web_page_preview=True)

    def fetch(self, bot, update):

        logger.info("Received message")

        self.set_message(update)
        self.set_chat_id(update)
        self.set_user_id(update)
        self.set_subreddit(bot)

        if self.subreddit is not None:
            self.get_submission()
            self.show_submission(bot)

    def error(self, bot, update, error):
        logger.warn('Update "%s" caused error "%s"' % (update, error))

    def set_message(self, update):
        self.message = update.message.text

    def set_chat_id(self, update):
        self.chat_id = update.message.chat_id

    def set_user_id(self, update):
        self.user_id = update.message.from_user.id        

    def set_subreddit(self, bot, name=None):

        if 'random' in self.message.lower().split():
            name = str(reddit.get_random_subreddit())
            bot.sendMessage(chat_id=self.chat_id, text=MSG_CHECKOUT+name)

        elif name is None:
            # clean up user message
            name = self.message.encode('ascii', 'ignore')
            name = name.lower()
            name = name.replace('moar ', '') # kb press sends this
            name = name.replace('/r/', '')
            name = ''.join(name.split())

        try:
            self.subreddit = reddit.get_subreddit(name)
            self.subreddit.fullname
        except:  # to-do: specify exceptions
            bot.sendMessage(chat_id=self.chat_id, text=MSG_INV_SUB)
            logger.warn("Invalid /r/%s" % name)
            self.subreddit = None

    def get_submission(self):

        def seen(submission):
            occurr = db['shown'].find_one(userid=self.user_id,
                                          subreddit=str(self.subreddit),
                                          submission=submission.id)
            if occurr is not None:
                return True
            else:
                return False

        def insert(submission):
            db['shown'].insert(dict(userid=self.user_id,
                              subreddit=str(self.subreddit),
                              submission=str(submission.id)))

        for submission in self.subreddit.get_hot(limit=None):
            if not seen(submission):
                self.submission = submission
                # to-do: insert only after successful delivery
                insert(submission)
                break

        logger.info("Fetched from /r/%s" % self.subreddit)

    def show_submission(self, bot):

        def make_snippet():
            url = self.submission.permalink.replace('www.reddit.', 'm.reddit.')
            comments = len(self.submission.comments)
            timestamp = getTimeAgo(self.submission.created_utc)
            return '<a href="%s">%d score, %d comments, %s</a>' % \
                        (url, self.submission.score, comments, timestamp)

        def make_keyboard():
            more_kb = []
            more_kb.append([MSG_MOAR+self.subreddit.display_name])
            more_kb.append([MSG_RANDOM])
            return telegram.ReplyKeyboardMarkup(more_kb,
                                                resize_keyboard=True,
                                                one_time_keyboard=True)

        # to-do: sanitize title for proper markup
        text = "[%s](%s)" % (self.submission.title, self.submission.url)
        bot.sendMessage(chat_id=self.chat_id,
                        text=text,
                        parse_mode=telegram.ParseMode.MARKDOWN)


        # send short link to reddit, no preview. also keyboard to continue
        bot.sendMessage(chat_id=self.chat_id,
                        text=make_snippet(),
                        reply_markup=make_keyboard(),
                        parse_mode=telegram.ParseMode.HTML,
                        disable_web_page_preview=True)

        logger.info("Shown https://redd.it/%s" % self.submission.id)


if __name__ == "__main__":
    RedditRobot()
