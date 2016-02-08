import tweepy
import sys
import pika
import json
import time

#get your own twitter credentials at dev.twitter.com
consumer_key = "yWgVrEgMvI7cUl1MchvfT4XDD"
consumer_secret = "5ERELN8CYErJIZcWJvHsA50czU9yURUZoTduOrjBvP3l9d10Ls"
access_token = "2915241117-MaKtqfHkmpuNjR3x6wh81TeSoNaFKvSJMH7ur8E"
access_token_secret = "BQP38brDOLr2afzoRnsk8P4lNtV52tEJGQz5IRb2fD3gP"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

class CustomStreamListener(tweepy.StreamListener):
    def __init__(self, api):
        self.api = api
        super(tweepy.StreamListener, self).__init__()

        credentials = pika.PlainCredentials('guest', 'guest')
		
        #setup rabbitMQ Connection
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost', credentials=credentials)
			
        )
        self.channel = connection.channel()

        #set max queue size
        args = {"x-max-length": 2000}

        self.channel.exchange_declare(exchange='twitter2', 
		                              type="direct" 
									  )
        self.channel.queue_declare(queue='twitter_topic_feed')

    def on_status(self, status):
        print(status.text)

        data = {}
        data['text'] = status.text
        data['created_at'] = time.mktime(status.created_at.timetuple())
        data['geo'] = status.geo
        data['source'] = status.source

        #queue the tweet
        self.channel.basic_publish(exchange='twitter2',
                                    routing_key='twitter_topic_feed',
                                    body=json.dumps(data))

    def on_error(self, status_code):
        print('Encountered error with status code:', status_code)
        return True  # Don't kill the stream

    def on_timeout(self):
        print('Timeout...')
        return True  # Don't kill the stream


def createStream():

    try:
        sapi = tweepy.streaming.Stream(auth, CustomStreamListener(api))
        sapi.filter(locations=[-10.9795,51.417,-5.4271,55.4015])  
        #Ireland -10.9795,51.417,-5.4271,55.4015
        #Galway -9.3535,53.1194,-8.4813,53.4559
    except UnicodeEncodeError as e:
        #print 'Unicode error, retry'
        createStream()
createStream()