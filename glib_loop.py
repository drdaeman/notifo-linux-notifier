import gobject
from tornado.ioloop import IOLoop
import logging

class GlibLoopImplementation(object):
    """
    A very simple Glib event loop integration for Tornado.
    Don't expect any performance.

    To use, pass this class' instance to `tornado.ioloop.IOLoop` constructor's
    `impl` argument. Consult Tornado source code and documentation for further
    details.
    """
    GLIB_EVENT_MAP = (
        (IOLoop.READ, gobject.IO_IN),
        (IOLoop.WRITE, gobject.IO_OUT),
        (IOLoop.ERROR, gobject.IO_ERR)
    )

    def __init__(self):
        self.logger = logging.getLogger("glib-loop")
        self.loop = gobject.MainLoop()
        self.sources = {}

    def register(self, fd, events):
        self.logger.debug("Registering %d with %d", fd, events)
        assert fd not in self.sources
        glib_events = 0
        for k, v in self.GLIB_EVENT_MAP:
            if events & k:
                glib_events |= v
        source_id = gobject.io_add_watch(fd, glib_events, self._on_event)
        self.sources[fd] = source_id

    def modify(self, fd, events):
        self.unregister(fd)
        self.register(fd, events)

    def unregister(self, fd):
        self.logger.debug("Unregistering %d", fd)
        gobject.source_remove(self.sources[fd])
        del self.sources[fd]

    def _glib_condition_name(self, condition):
        names = set()
        for name in dir(gobject):
            if name.startswith('IO_') and not '_' in name[3:]:
                value = getattr(gobject, name)
                if condition & value:
                    names.add(name)
        return "+".join(names)

    def _on_event(self, fd, condition, user_data=None):
        self.logger.debug("Events %d (%s) for %d", condition,
                          self._glib_condition_name(condition), fd)
        self.events[fd] = 0
        for k, v in self.GLIB_EVENT_MAP:
            if condition & v:
                self.events[fd] |= k
        self.loop.quit()
        return True

    def _on_timeout(self, user_data=None):
        self.loop.quit()
        return False

    def poll(self, timeout):
        self.events = {}
        gobject.timeout_add(int(timeout * 1000), self._on_timeout)
        self.loop.run()
        if len(self.events) > 0:
            self.logger.debug("Got events: %r", self.events)
        return self.events
