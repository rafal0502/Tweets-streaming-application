from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import API
from tweepy import Stream
import json
import time
from threading import Lock, Timer
from textblob import TextBlob
from unidecode import unidecode
import sqlite3
import twitter_credentials
import psycopg2


conn = sqlite3.connect('twitter.db', check_same_thread=False, isolation_level=None)
c = conn.cursor()


def create_table():
    try:
        c.execute("PRAGMA journal_mode=wal")
        c.execute("PRAGMA wal_checkpoint=TRUNCATE")
        c.execute('CREATE TABLE IF NOT EXISTS tweets_base'
                  '('
                  'key_search TEXT,'
                  'sentiment REAL,'
                  'created_at DATETIME, '
                  'username TEXT, '
                  'user_screenname TEXT, '
                  'text TEXT, '
                  'user_followers_count INTEGER, '
                  'user_friends_count INTEGER, '
                  'profile_image  BLOB,'
                  'location BLOB,'
                  'user_url  BLOB,'
                  'reply_count INTEGER,'
                  'user_created_at DATETIME,'
                  'favorite_count INTEGER, '
                  'retweet_count INTEGER, '
                  'user_favourites_count INTEGER, '
                  'verified BLOB, '
                  'lang TEXT, '  
                  'unix_time REAL,'
                  'tweet_id REAL'
                  ')')  
        c.execute("CREATE INDEX fast_key_search ON tweets_base(key_search)")
        c.execute("CREATE INDEX fast_tweet_id ON tweets_base(tweet_id)")
        c.execute("CREATE INDEX fast_username ON tweets_base(username)")
        c.execute("CREATE INDEX fast_created_at ON tweets_base(created_at)")
        c.execute("CREATE INDEX fast_text ON tweets_base(text)")
        c.execute("CREATE INDEX fast_favorite_count ON tweets_base(favorite_count)")
        c.execute("CREATE INDEX fast_retweet_count ON tweets_base(retweet_count)")
        c.execute("CREATE INDEX fast_user_followers_count ON tweets_base(user_followers_count)")
        c.execute("CREATE INDEX fast_reply_count ON tweets_base(reply_count)")
        c.execute("CREATE INDEX fast_user_friends_count ON tweets_base(user_friends_count)")
        c.execute("CREATE INDEX fast_profile_image ON tweets_base(profile_image)")
        c.execute("CREATE INDEX fast_user_favourites_count ON tweets_base(user_favourites_count)")
        c.execute("CREATE INDEX fast_location ON tweets_base(location)")
        c.execute("CREATE INDEX fast_verified ON tweets_base(verified)")
        c.execute("CREATE INDEX fast_user_url ON tweets_base(user_url)")
        c.execute("CREATE INDEX fast_lang ON tweets_base(lang)")
        c.execute("CREATE INDEX fast_user_created_at ON tweets_base(user_created_at)")
        c.execute("CREATE INDEX fast_user_screenname ON tweets_base(user_screenname)")
        c.execute("CREATE INDEX fast_sentiment ON tweets_base(sentiment)")
        c.execute("CREATE INDEX fast_unix_time ON tweets_base(unix_time)")
        conn.commit()
    except Exception as e:
        print(str(e))


create_table()
lock = Lock()


class TwitterAuthenticator:

    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth


class TwitterStreamer():
    """
    Class for streaming and processing live tweets.
    """
    def __init__(self):
        self.twitter_authenticator = TwitterAuthenticator()
        self.stream = None

    def start_stream(self, hash_tag_list, key_search):
        # This handles Twitter authetification and the connection to Twitter Streaming API
        listener = TwitterListener(lock, key_search)
        auth = self.twitter_authenticator.authenticate_twitter_app()
        stream = Stream(auth, listener)

        # This line filter Twitter Streams to capture data by the keywords:
        stream.filter(track=hash_tag_list, async=True)

    def stop_stream(self):
        self.stream.disconnect()


class TwitterListener(StreamListener):
    """
    This is a basic listener that just prints received tweets to stdout.
    """
    data = []
    lock = None

    def __init__(self, lock, key_search):
        # create lock
        self.lock = lock
        self.key_search = key_search
        # init timer for database save
        self.save_in_database()
        # call __init__ of super class
        super().__init__()

    def save_in_database(self):

        # set a timer (1 second)
        Timer(1, self.save_in_database).start()

        # with lock, if there's data, save in transaction using one bulk query
        with self.lock:
            if len(self.data):
                c.execute('BEGIN TRANSACTION')
                try:
                    c.executemany('INSERT INTO tweets_base ('
                    'key_search,'
                    'sentiment,'
                    'username, '
                    'created_at, '
                    'text, '
                    'tweet_id, '
                    'favorite_count, '
                    'retweet_count, '
                    'user_followers_count, '
                    'user_url, '
                    'user_friends_count, '
                    'user_favourites_count,'
                    'user_created_at, '
                    'user_screenname,'
                    'lang, '
                    'reply_count,'
                    'verified, '
                    'profile_image, '
                    'location, '
                    'unix_time) '
                    'VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',self.data)
                except:
                    pass
                c.execute('COMMIT')

                self.data = []

    def on_data(self, data):
        try:
            data = json.loads(data)
            key_search = self.key_search
            tweet_id = data['id']
            created_at = data['created_at']
            username = data['user']['name']
            text = unidecode(data['text'])
            reply_count = data['reply_count']
            favorite_count = data['favorite_count']
            retweet_count = data['retweet_count']
            user_followers_count = data['user']['followers_count']
            user_friends_count = data['user']['friends_count']
            user_favourites_count = data['user']['favourites_count'] # polubienia użytkownika
            profile_image = data['user']['profile_image_url_https']
            location = data['user']['location']
            verified = data['user']['verified']
            user_url = data['user']['url']
            lang = data['user']['lang']
            user_created_at = data['user']['created_at']
            user_screenname = data['user']['screen_name']
            unix_time = data['timestamp_ms']
            analysis = TextBlob(text)
            sentiment = analysis.sentiment.polarity
            #print("Gotcha")
            # print(" Data:", created_at, "Użytkownik:", username, user_screenname, "Sentyment", sentiment,
            #       "Tekst:", text[:50], "Polubienia:", favorite_count, "Retweety:", retweet_count,
            #       "Obserwujacy:", user_followers_count, "Obserwowani:", user_friends_count)

            # append to data list (to be saved every 1 second)
            with self.lock:
                self.data.append((key_search, sentiment, username, created_at, text, tweet_id, favorite_count,
                                  retweet_count, user_followers_count, user_url, user_friends_count,
                                  user_favourites_count,user_created_at,user_screenname,lang,
                                  reply_count,verified,profile_image,location,unix_time))

        except KeyError as e:
            # print(data)
            with open('on_data_errors.txt', 'a') as f:
                f.write(str(e))
                f.write('\n')
        return True

    def on_error(self, status):
        if status == 420:
            # Returning False on_data method in case rate limit occurs.
            with open('on_error_message.txt', 'a') as f:
                f.write("Status 420")
                f.write('\n')
            return False


#
# #
# if __name__ == '__main__':
#     hash_tag_list = ["Google"]
# while True:
#     # time.sleep(10)
#     try:
#         twitter_streamer = TwitterStreamer()
#         twitter_streamer.start_stream(hash_tag_list, hash_tag_list)
#     except Exception as e:
#         print(str(e))
#         time.sleep(5)


# class Streaming_thread():
#     def __init__(self):
#         self._running = True
#
#     def terminate(self):
#         self._running = False
#
#     def run(self):
#         hash_tag_list = ["a", "e", "i", "o"]
#         while self._running:
#             try:
#                 twitter_streamer = TwitterStreamer()
#                 twitter_streamer.stream_tweets(hash_tag_list)
#             except Exception as e:
#                 print(str(e))
#                 time.sleep(5)

