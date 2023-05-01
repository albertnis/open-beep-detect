from autobahn.twisted.websocket import WebSocketServerProtocol


class AudioServerProtocol(WebSocketServerProtocol):
    connected_instances: list['AudioServerProtocol'] = []

    def onConnect(self, request):
        self.connected_instances.append(self)
        print("Client connecting: {}".format(request.peer))
        print("There are ", len(self.connected_instances), " connected instances")

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {} bytes".format(len(payload)))
        else:
            print("Text message received: {}".format(payload.decode('utf8')))

        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        self.connected_instances.remove(self)
        print("WebSocket connection closed: {}".format(reason))

    @classmethod
    def sendMessageOnAllInstances(cls, payload):
        print("There are ", len(cls.connected_instances), " connected instances")
        for c in set(cls.connected_instances):
            print('sending payload ', payload, ' to connection ', c.__hash__)
            c.sendMessage(bytes(payload, encoding='utf8'))