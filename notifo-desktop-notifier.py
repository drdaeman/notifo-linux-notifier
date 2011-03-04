#!/usr/bin/env python

"""
A simple tool, which connects to AMQP broker, listens for messages
sent by `webhook.py` server and displays notifications with libnotify.
"""

import sys
import os.path
import pynotify
import stormed
import tornado.ioloop
import logging
import json

import config

default_icon = "file://" + os.path.abspath(os.path.join(
    os.path.dirname(__file__), "notifo.png"))
amqp_channel = None
logging.basicConfig()

def on_amqp_connect():
    """
    Callback called when AMQP connection's established.
    """
    global amqp_channel
    amqp_channel = amqp_connection.channel()
    amqp_channel.exchange_declare(exchange="notifo", type="fanout")
    amqp_channel.queue_declare(exclusive=True, callback=on_queue_declared)

def on_queue_declared(qinfo):
    """
    Callback called when an queue is declared.
    """
    amqp_channel.queue_bind(exchange="notifo", queue=qinfo.queue)
    amqp_channel.consume(qinfo.queue, on_message, no_ack=True)

def on_message(message):
    """
    Callback called when we receive AMQP message.
    """
    try:
        data = json.loads(message.body)
    except:
        #print "failed to parse %s" % message.body
        return
    title = data.get("title", None)
    if title is not None:
        title = u"Notifo \u2014 " + title
    else:
        title = u"Notifo"
    message = data.get("message", u"")\
                  .replace(u"&", "&amp;")\
                  .replace(u"<", u"&lt")\
                  .replace(">", "&gt;")
    uri = data.get("uri", None)
    if uri is not None:
        message += u"\n\n<i>" + uri + u"</i>"
    # TODO: Support more stuff (icons, priorities etc.)
    notification = pynotify.Notification(
        title,
        message,
        default_icon
    )
    notification.show()

if __name__ == "__main__":
    if not pynotify.init("Notifo"):
        print("Failed to initialize libnotify")
        sys.exit(1)
    amqp_connection = stormed.Connection(**config.amqp)
    amqp_connection.connect(on_amqp_connect)
    ioloop = tornado.ioloop.IOLoop.instance()
    try:
        ioloop.start()
    except KeyboardInterrupt:
        amqp_connection.close(ioloop.stop)
