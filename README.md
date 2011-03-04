Notifo.com notifications for GNU/Linux desktops
===============================================

At date this document's written (2011-03-04), Notifo.com doesn't provide any
GNU/Linux client software.

However, they provide "notification webhooks", where they'd POST notification
data each time a notification's delivered to user account.

This repository contains two simple utilities:

  - `notifo-webhook-server.py`, which receives notifications using HTTP and
    publishes them to AMQP server (tested with RabbitMQ).
  - `notifo-desktop-notifier.py`, which consumes messages from AMQP server
    and displays them using libnotify.

Set up first one along with AMQP server to run somewhere publicily accessible
from the Internet, and run second one on your desktop. Hopefully, things
should work.

The code was written in an hour or two, so it contain bugs and lack features.
However, it works for me. Feel free to contribute.

License (Expat ("MIT") license)
-------------------------------

Copyright (c) 2011 by Aleksey Zhukov

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is furnished
to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

The software is provided "as is", without warranty of any kind, express or
implied, including but not limited to the warranties of merchantability,
fitness for a particular purpose and noninfringement. In no event shall the
authors or copyright holders be liable for any claim, damages or other
liability, whether in an action of contract, tort or otherwise, arising from,
out of or in connection with the software or the use or other dealings in
the software.
