# Telegram Bot for Reddit

![](https://raw.githubusercontent.com/danlou/telegram-reddit/master/screenshots/rdtg1.jpg)

![](https://raw.githubusercontent.com/danlou/telegram-reddit/master/screenshots/rdtg2.jpg)

This Telegram bot is the lightest way to explore reddit submissions, from any subreddit of the user's choosing.

It's a simple python project that ties together reddit's and Telegram's APIs, using PRAW and python-telegram-bot, respectively.

It was designed to be lightweight and more of viewer than a full-featured client.

If you want to try it out, it's up and running [here](https://telegram.me/RedditRobot)

## Deploy your own

To deploy your own bot, first follow [Telegram's instructions](https://telegram.me/botfather) to get your token.
After than, make the necessary adjustments to config.py, install dependencies in requirements.txt and execute bot.py.

Note that this project requires a database to keep track of submissions that a user has already seen before (the database only stores the user's id number, meaning that this data is anonymous). It's in production with sqlite3, but it uses the [dataset](https://dataset.readthedocs.org) library, so you should be fine using any other database supported by dataset.