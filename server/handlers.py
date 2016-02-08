# -*- coding: utf-8 -*-

import tornado.escape
import tornado.web
import tornado.websocket
from tornado import httpclient

from uuid import uuid4


class IndexHandler(tornado.websocket.WebSocketHandler):

    def open(self, *args, **kwargs):
        self.application.rmanager.add_event_listener(self)
        print("WebSocket opened")
 
    def on_close(self):
        print("WebSocket closed")
        self.application.rmanager.remove_event_listener(self)


class ConsumerHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        self.application.dispatcher.register(self.callback)

    def on_close(self):
        self.application.dispatcher.unregister(self.callback)

    def on_message(self, message):
        pass

    def callback(self, msg):
        self.write_message('{"msg":"%s"}' % msg)
