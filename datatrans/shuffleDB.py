from mongoengine import *
from random import shuffle
from pymongo import MongoClient
from itertools import zip_longest


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


shuffled_db = connect('shuffled_DB')

# drop the database once to ensure whenever the thread is run, we create the db afresh
shuffled_db.drop_database('shuffled_DB')

client = MongoClient()
final_db = client.Final_db

# get data for training...

news_tweet_count = 0  # no of fetched news tweets
misc_tweet_count = 0  # no of fetched miscellaneous tweets
news_tweet_fetch_lmt = 100  # no of news tweets to be retrieved from DB at a time
misc_tweet_fetch_lmt = 100  # no of misc tweets to be retrieved from DB at a time
total_news_lmt = 316823  # total news tweets to be retrieved
total_misc_lmt = 316823  # total misc tweets to be retrieved
total_tweets = []  # final list having all the tweets
tweet_id = []  # a temp list to store IDs of chunk of news/misc tweets fetched
cursor = None
group_size = 10000
count = 0
temp_list = []

while news_tweet_count < total_news_lmt and misc_tweet_count < total_misc_lmt and total_news_lmt - news_tweet_count > news_tweet_fetch_lmt and total_misc_lmt - misc_tweet_count > misc_tweet_fetch_lmt:
    cursor = final_db.Tweets.find({}, {'_id': 1}).sort("_id", 1).skip(news_tweet_count).limit(news_tweet_fetch_lmt)

    news_tweet_count += news_tweet_fetch_lmt

    # append news tweets to a temp list
    for record in cursor:
        tweet_id.append(record['_id'])

    cursor = final_db.Tweets.find({}, {'_id': 1}).sort("_id", -1).skip(misc_tweet_count).limit(misc_tweet_fetch_lmt)

    misc_tweet_count += misc_tweet_fetch_lmt

    # append misc tweets to temp list
    for record in cursor:
        tweet_id.append(record['_id'])

    # shuffle the retrieved news+misc tweets
    shuffle(tweet_id)

    # for t in final_db.Tweets_data.find({'_id' : {'$in': tweet_id}}):
    # 	print t['is_news']

    for tweet in tweet_id:
        total_tweets.append(tweet)

    if len(total_tweets) > 1000:
        cursor = final_db.Tweets.find({'_id': {'$in': total_tweets}})
        count += cursor.count(with_limit_and_skip=True)

        print('Processed {0} tweets in total'.format(count))

        for record in cursor:
            record.pop("_id", None)
            temp_list.append(record)
        shuffle(temp_list)
        shuffled_db.shuffled_DB.Labeled_Tweets.insert(temp_list)
        total_tweets = []
        temp_list = []
    tweet_id = []

tweet_id = []
total_tweets = []

# fetch remaining news tweets
news_tweet_fetch_lmt = total_news_lmt - news_tweet_count
cursor = final_db.Tweets.find({}, {'_id': 1}).sort("_id", 1).skip(news_tweet_count).limit(news_tweet_fetch_lmt)
for record in cursor:
    tweet_id.append(record['_id'])

# fetch remaining misc tweets
misc_tweet_fetch_lmt = total_misc_lmt - misc_tweet_count
cursor = final_db.Tweets.find({}, {'_id': 1}).sort("_id", -1).skip(misc_tweet_count).limit(misc_tweet_fetch_lmt)
for record in cursor:
    tweet_id.append(record['_id'])

# shuffle the list
shuffle(tweet_id)

# fetch and store in new DB
temp_list = []
cursor = final_db.Tweets.find({'_id': {'$in': tweet_id}})
count += cursor.count(with_limit_and_skip=True)
for record in cursor:
    record.pop("_id", None)
    temp_list.append(record)
shuffle(temp_list)
shuffled_db.shuffled_DB.Labeled_Tweets.insert(temp_list)
total_tweets = []
