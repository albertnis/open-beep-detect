import sys

from twisted.python import log
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from autobahn.twisted.websocket import WebSocketServerFactory

from autobahn.twisted.resource import WebSocketResource, WSGIRootResource

from .app import app
from .ws import AudioServerProtocol

from multiprocessing import Process
import threading

log.startLogging(sys.stdout)

wsFactory = WebSocketServerFactory("ws://localhost:8080")
wsFactory.protocol = AudioServerProtocol
wsResource = WebSocketResource(wsFactory)

wsgiResource = WSGIResource(reactor, reactor.getThreadPool(), app)

rootResource = WSGIRootResource(wsgiResource, { b'ws': wsResource })

site = Site(rootResource)

def count_connections():
    print("There are ", len(AudioServerProtocol.connected_instances), " connected instances")

def schedule_send(num):
    print('Num is ', num)
    threading.Timer(1, schedule_send, (num + 1,)).start()
    reactor.callFromThread(AudioServerProtocol.sendMessageOnAllInstances, str(num))

reactor.callInThread(schedule_send, 1)

reactor.listenTCP(8080, site)
reactor.run()