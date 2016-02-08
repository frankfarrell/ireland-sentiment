# -*- coding: utf-8 -*-

import logging
import json

import pika
from pika.adapters.tornado_connection import TornadoConnection
import tornado.httpserver
import tornado.ioloop
import tornado.web

from server.tweetclassifier import Classifier

class PikaClient(object):

    def __init__(self, config, app=None):
        self.classifier = Classifier()
        # Connection params
        self.host = config['host'] or 'localhost'
        self.port = config['port'] or '5672'
        self.vhost = config['vhost'] or '/'
        self.user = config['user'] or 'guest'
        self.passwd = config['passwd'] or 'guest'
        self.exchange = config['exchange'] or 'twitter2'
        self.queue_name = config['queue_name'] or 'twitter_topic_feed'
        self.routing_key = config['routing_key'] or 'twitter_topic_feed'

        # Default values
        self.connected = False
        self.connecting = False
        self.connection = None
        self.channel = None

        self.app = app
        self.event_listeners = set([])
        # A place for us to keep messages sent to us by Rabbitmq
        self.messages = list()

        # A place for us to put pending messages while we're waiting to connect
        self.pending = list()

        self.connect()

    def connect(self):
        if self.connecting:
            print('PikaClient: Already connecting to RabbitMQ')
            return
        print('PikaClient: Connecting to RabbitMQ on %s:%i' \
            % (self.host, self.port))
        self.connecting = True

        credentials = pika.PlainCredentials(self.user, self.passwd)

        param = pika.ConnectionParameters(host=self.host, port=self.port,
            virtual_host=self.vhost, credentials=credentials)

        logging.debug('Events: Connecting to AMQP Broker: %s:%i' % (self.host,
            self.port))

        # from pika.adapters import SelectConnection
        # connection = SelectConnection(parameters, on_connected)
        self.connection = TornadoConnection(param,
            on_open_callback=self.on_connected)

        self.connection.add_on_close_callback(self.on_closed)

    def on_connected(self, connection):
        print('PikaClient: Connected to RabbitMQ on %s:%i' \
            % (self.host, self.port))

        self.connected = True
        self.connection = connection
        self.connection.channel(self.on_channel_open)

    def on_channel_open(self, channel):
        print('PikaClient: Channel Open, Declaring Exchange %s' \
            % self.exchange)

        self.channel = channel
        self.channel.exchange_declare(exchange=self.exchange,
                                      type="direct",
                                      durable=False,
                                      callback=self.on_exchange_declared)

    def on_exchange_declared(self, frame):
        print('PikaClient: Exchange Declared, Declaring Queue %s' \
            % self.queue_name)
        self.channel.queue_declare(queue=self.queue_name,
                                   durable=False,
                                   exclusive=False,
                                   callback=self.on_queue_declared)

    def on_queue_declared(self, frame):
        print('PikaClient: Queue Declared, Binding Queue')
        self.channel.queue_bind(exchange=self.exchange,
                                queue=self.queue_name,
                                routing_key=self.routing_key,
                                callback=self.on_queue_bound)

    def on_queue_bound(self, frame):
        print('PikaClient: Queue Bound, Issuing Basic Consume')
        self.channel.basic_consume(consumer_callback=self.on_message,
                                   queue=self.queue_name,
                                   no_ack=True)
        # Send any messages pending
        for properties, body in self.pending:
            self.channel.basic_publish(exchange=self.exchange,
                                       routing_key=self.routing_key,
                                       body=body,
                                       properties=properties)

    def on_basic_cancel(self, frame):
        print('PikaClient: Basic Cancel Ok')
        # If we don't have any more consumer processes running close
        self.connection.close()

    def on_closed(self, connection):
        # We've closed our pika connection so stop the demo
        tornado.ioloop.IOLoop.instance().stop()

    def on_message(self, channel, method, header, body):
        print('PikaCient: Message received: %s delivery tag #%i: %s' \
           % (header.content_type, method.delivery_tag, body))

        # Append it to our messages list
        self.messages.append(body)

        self.app.dispatcher.notifyCallbacks(body)
        self.notify_listeners(body)
    
    def notify_listeners(self, event_obj):
        # here we assume the message the sourcing app
        # post to the message queue is in JSON format
        event_json = self.classify_text(event_obj)
        for listener in self.event_listeners: 
            listener.write_message(event_json)
            print('PikaClient: notified %s' % repr(listener))
 
    def add_event_listener(self, listener):
        self.event_listeners.add(listener)
        print('PikaClient: listener %s added' % repr(listener))
 
    def remove_event_listener(self, listener):
        try:
            self.event_listeners.remove(listener)
            print('PikaClient: listener %s removed' % repr(listener))
        except KeyError:
            pass

    def get_messages(self):
        # Get the messages to return, then empty the list
        output = self.messages
        self.messages = list()
        return output

    def publish(self, msg):
        # Build a message to publish to RabbitMQ
        #body = '%.8f: Request from %s [%s]' % \
        #       (tornado_request._start_time,
        #        tornado_request.remote_ip,
        #        tornado_request.headers.get("User-Agent"))

        # Send the message
        properties = pika.BasicProperties(content_type="text/plain",
                                          delivery_mode=1)
        self.channel.basic_publish(exchange=self.exchange,
                                   routing_key=self.routing_key,
                                   #body='Message: %s - %s' % (msg, body),
                                   body='Message: %s' % msg,
                                   properties=properties)
    
    def classify_text(self,event_json):
        #Temporaray: Processing should happen in intermediary handler
        #Parse JSON, return JSON with text geo and polarity
        print("CLASSIFIER MESSAGE " + event_json)
        parsedJson  =json.loads(event_json)
        tweettext = parsedJson['text'] 
        tweetgeo = parsedJson['geo']
        #tweetplace = parsedJson['place']
        #tweetcoords = parsedJson['coordinates']		
        tweet_polarity = self.classifier.classify(tweettext)
        return {'text':tweettext, 'geo': tweetgeo, 'polarity':tweet_polarity}#, 'place':tweetplace,'coordinates':tweetcoords}