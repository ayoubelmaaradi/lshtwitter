#!/usr/bin/env python
import pika
import time
import json
import numpy as np
from sklearn import metrics
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
import pickle
import os
import utils

connection        = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel           = connection.channel()
project_root      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_dump_path   = os.path.join(project_root, 'Classifier Models', 'Naive Bayes')
count_vect        = None
tfidf_transformer = None
clf               = None
total_news        = 0
total_non_news    = 0
total_tweets      = 0

# declare all queues
# ProjectName.Q.<Environment>.<ConsumerName>.MessageTypeName
channel.queue_declare(queue='FYP.Q.Filter.TweetMessage', durable=False)
channel.queue_declare(queue='FYP.Q.NearestNeighbour.NewsTweetMessage', durable=True)
channel.queue_declare(queue='FYP.Q.Generic.NonNewsTweetMessage', durable=True)

# declare exchange along with its type
channel.exchange_declare(exchange='tweets', type='direct')

# bind exchange to our queues
channel.queue_bind(exchange='tweets', queue="FYP.Q.NearestNeighbour.NewsTweetMessage", routing_key='news')
channel.queue_bind(exchange='tweets', queue="FYP.Q.Generic.NonNewsTweetMessage", routing_key='non_news')


print('[*] Waiting for messages. To exit press CTRL+C')

# initialize models here(saved to disk already)
models = [['count_vect.60_40.0.886620715777.plk',
'tfidf_transformer.60_40.0.886620715777.plk',
'clf.60_40.0.886620715777.plk'],
['count_vect.80_20.0.908758689176.plk',
'tfidf_transformer.80_20.0.908758689176.plk',
'clf.80_20.0.908758689176.plk'],
['count_vect.80_20.0.922510427011.plk',
'tfidf_transformer.80_20.0.922510427011.plk',
'clf.80_20.0.922510427011.plk']
]

# Change the model index to use a different model
model_index = 2

def loadModels():
    
    global count_vect, tfidf_transformer, clf

    print("filter: Loading Models ...")
    with open(os.path.join(model_dump_path, models[model_index][0]), "rb") as fid:
        count_vect = pickle.load(fid)

    with open(os.path.join(model_dump_path, models[model_index][1]), "rb") as fid:
        tfidf_transformer = pickle.load(fid)

    with open(os.path.join(model_dump_path, models[model_index][2]), "rb") as fid:
        clf = pickle.load(fid)
    print("filter: Models loaded!")
    
    
def callback(ch, method, properties, body):
    global total_tweets, total_news, total_non_news
    total_tweets   = total_tweets + 1
    json_tweet     = json.loads(body)
    text           = json_tweet['tweet']
    sanitized_text = utils.cleanThis(text)
    X_new_counts   = count_vect.transform([sanitized_text])
    X_new_tfidf    = tfidf_transformer.transform(X_new_counts)
    predicted      = clf.predict(X_new_tfidf)
    
    # add sanitized text to msg body
    json_tweet['sanitized_text'] = sanitized_text

    if predicted[0] == 1:
        # send news to News queue - FYP.Q.Cluster.NearestNeighbour
        channel.basic_publish(exchange='tweets', routing_key='news', body=json.dumps(json_tweet))

        total_news = total_news + 1

        # if ner.checkNER([sanitized_text]):
        #     print(" [x] NER Received %r" % text)
            
        # else:
        #     print(" [x] Received %r" % text)
    

    else:
        # send news to None-News queue FYP.Q.Generic.NonNewsTweetMessage
        channel.basic_publish(exchange='tweets', routing_key='non_news', \
                              body=json.dumps(json_tweet))
        total_non_news = total_non_news + 1                             
    
    if total_tweets % 100 == 0:
        print(total_news)
        print(total_non_news)
        
    # acknowledge the sender (streamer)
    ch.basic_ack(delivery_tag = method.delivery_tag)


if __name__ == '__main__':
    loadModels()
    channel.basic_qos(prefetch_count=10)
    channel.basic_consume(callback,queue='FYP.Q.Filter.TweetMessage')
    channel.start_consuming()

