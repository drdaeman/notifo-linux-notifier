#!/usr/bin/env python

"""
A simple tool, which connects to AMQP broker, listens for messages
sent by `webhook.py` server and displays notifications with libnotify.
"""

import sys
import os.path
import pynotify
import indicate
import gobject
import stormed
import tornado.ioloop
import logging
import json
import time
import webbrowser

logging.basicConfig()

import config
import glib_loop

local_path = lambda *path: os.path.abspath(os.path.join(
    os.path.dirname(__file__), *path))
default_icon = "file://" + local_path("notifo.png")
amqp_channel = None
indicators = {}

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
    print(repr(data))
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
    if uri is not None and uri != u"subscribe_request":
        message += u"\n\n<i>" + uri + u"</i>"
    # TODO: Support more stuff (icons, priorities etc.)
    notification = pynotify.Notification(
        title,
        message,
        default_icon
    )
    notification.show()
    if uri is not None:
        if uri == u"subscribe_request":
            uri = u"http://notifo.com/user"
        add_indicator(title, uri)

def on_server_click(server, *args):
    """
    Callback called when our Messaging menu main entry's clicked
    """
    global indicators
    for indicator in indicators.itervalues():
        indicator[0].hide()
    indicators = {}
    webbrowser.open("http://notifo.com/user")

def on_indicator_click(indicator, *args):
    """
    Callback called when our Messaging menu indicator entry clicked
    """
    label = indicator.get_property("label")
    assert label is not None
    if type(label) is str:
        label = label.decode("utf-8")
    assert label in indicators
    indicator = indicators[label][0]
    last_event = indicators[label].pop()
    if len(indicators[label]) < 2:
        indicator.hide()
        del indicators[label]
    else:
        indicator.set_property("count", str(len(indicators[label]) - 1))
    if "uri" in last_event:
        webbrowser.open(last_event["uri"])

def add_indicator(label, uri=None):
    """
    Adds new indicator entry to Messaging menu.
    """
    if label not in indicators:
        indicator = indicate.Indicator()
        indicator.set_property("name", label)
        indicator.set_property("label", label)
        indicator.set_property("draw-attention", "true")
        indicator.set_property("count", "1")
        indicator.set_property_time("time", time.time())
        indicator.connect("user-display", on_indicator_click)
        indicator.show()
        indicators[label] = [indicator, {"uri": uri}]
    else:
        indicator = indicators[label][0]
        indicators[label].append({"uri": uri})
        indicator.set_property("count", str(len(indicators[label]) - 1))

def setup_indicate():
    """
    Sets up Messaging menu
    """
    global indicators
    server = indicate.indicate_server_ref_default()
    server.set_type("message.mail")
    server.set_desktop_file(local_path("notifo.desktop"))
    server.connect("server-display", on_server_click)
    server.show()
    indicators = {}

if __name__ == "__main__":
    if not pynotify.init("Notifo"):
        print("Failed to initialize libnotify")
        sys.exit(1)
    setup_indicate()
    io_loop = tornado.ioloop.IOLoop(impl=glib_loop.GlibLoopImplementation())
    amqp_connection = stormed.Connection(io_loop=io_loop, **config.amqp)
    amqp_connection.connect(on_amqp_connect)
    try:
        io_loop.start()
    except KeyboardInterrupt:
        amqp_connection.close(io_loop.stop)
