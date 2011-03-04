#!/usr/bin/env python

"""
A simple webhook for Notifo.com, which publishes messages to AMQP exchange.
All configuration is done in `config.py` (keep this file private).

Requires Tornado and Stormed-AMQP.
"""

import tornado.ioloop
import tornado.web
import stormed
import hashlib
import urllib
import json

import config

def simple_arg_value(value):
    """
    Returns a specific-purporse suitable representation of
    an Tornado-provided GET/POST argument.

    Flattens lists if there's only one item, and converts
    unicode strings to UTF-8.
    """
    if type(value) in (list, tuple) and len(value) == 1:
        value = value[0]
    if type(value) is unicode:
        value = value.encode("utf-8")
    return value

def compute_signature(api_secret, post_data):
    """
    Given an API secret and dictionary of POSTed data with "notifo_"
    prefix stripped, calculate the "signature" as defined
    here: https://api.notifo.com/docs/webhooks

    Returned is SHA-1 "signature", as a hex string in lowercase.
    """
    shash = hashlib.sha1()
    for key in sorted(post_data.keys()):
        #if key == "signature": # or not key.startswith("notifo_"):
        #    continue
        value = post_data[key]
        if not type(value) is str:
            raise ValueError, "Value must be a bytestring, not %s" % \
                              repr(type(value))
        shash.update(urllib.quote(value, safe=""))
    shash.update(urllib.quote(api_secret, safe=""))
    return shash.hexdigest().lower()

def on_amqp_connect():
    """
    Callback, called when AMQP connection is established.
    Decares an exchange
    """
    global application
    amqp_channel = amqp_connection.channel()
    amqp_channel.exchange_declare(exchange="notifo", type="fanout")
    application.amqp_channel = amqp_channel

class NotifoWebhookHandler(tornado.web.RequestHandler):
    """
    Handles Notifo's POST requests.
    """
    def post(self):
        data = dict((k[7:], simple_arg_value(v))
                    for k, v in self.request.arguments.iteritems()
                    if k.startswith("notifo_") and k != "notifo_signature")
        signature_have = self.get_argument("notifo_signature", "").lower()
        signature_must = compute_signature(config.api_secret, data)
        if signature_have != signature_must:
            raise tornado.web.HTTPError(403)
        msg = stormed.Message(json.dumps(data), delivery_mode=2)
        if application.amqp_channel is not None:
            application.amqp_channel.publish(msg, exchange="notifo",
                                             routing_key="")
        self.set_header("Content-Type", "text/plain; charset=utf-8")
        self.write("Got it.\n")

application = tornado.web.Application([
    (r"/notifo-hook", NotifoWebhookHandler),
])

if __name__ == "__main__":
    application.listen(config.bind_port)
    application.amqp_channel = None
    amqp_connection = stormed.Connection(**config.amqp)
    amqp_connection.connect(on_amqp_connect)
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()
