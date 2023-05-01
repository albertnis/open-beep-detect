import sys

from threading import Event

from twisted.python import log
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from autobahn.twisted.websocket import WebSocketServerFactory

from autobahn.twisted.resource import WebSocketResource, WSGIRootResource

from .app import app
from .ws import AudioServerProtocol

import threading

log.startLogging(sys.stdout)

wsFactory = WebSocketServerFactory("ws://localhost:8080")
wsFactory.protocol = AudioServerProtocol
wsResource = WebSocketResource(wsFactory)

wsgiResource = WSGIResource(reactor, reactor.getThreadPool(), app)

rootResource = WSGIRootResource(wsgiResource, { b'ws': wsResource })

site = Site(rootResource)

stopping = Event()

def schedule_send(num, stop_event):
    if not stop_event.is_set():
        print('Num is ', num)
        print('Stopping is ', stopping)
        threading.Timer(1, schedule_send, (num + 1, stop_event)).start()
        reactor.callFromThread(AudioServerProtocol.sendMessageOnAllInstances, str(num))

reactor.callInThread(schedule_send, 1, stopping)

reactor.listenTCP(8080, site)
reactor.addSystemEventTrigger('before', 'shutdown', lambda: stopping.set())
reactor.run()