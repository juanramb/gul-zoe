import socket
import threading
import configparser
from zoe.zp import *
from zoe.listener import *
from zoe.ptp import *
from zoe.topic import *

class Server:
    def __init__(self,                         \
                 host = "localhost",           \
                 port = 30000,                 \
                 configstr = None,             \
                 configfile = None):
        self._dispatchers = []
        self._agents = {}
        self._listener = Listener(host, port, self, host, port)
        self._config = configparser.ConfigParser()
        if configfile:
            self._config.read(configfile)
        if configstr:
            self._config.read_string(configstr)
        self.registerAgents()
        self.registerDispatcher(PTPDispatcher(self._config))
        self.registerDispatcher(TopicDispatcher(self._config))

    def start(self):
        self._listener.start()

    def stop(self):
        self._listener.stop()

    def registerAgents(self):
        for section in self._config.sections():
            sectype, secname = section.split(" ")
            if sectype == "agent":
                host = self._config[section]["host"]
                port = int(self._config[section]["port"])
                self.registerAgent (secname, host, port)

    def registerDispatcher(self, dispatcher):
        self._dispatchers.append(dispatcher)

    def registerAgent(self, name, host, port):
        self._agents[name] = (host, port)

    def destinationFor (self, parser):
        for dispatcher in self._dispatchers:
            destination = dispatcher.dispatch(parser)
            if destination: return destination

    def agentFor (self, parser):
        destination = self.destinationFor(parser)
        if not destination: return None
        if destination.__class__ is str:
            destination = [destination]
        agents = []
        for peer in destination:
            if peer in self._agents:
                agents.append (self._agents[peer])
        return agents

    def dispatch(self, parser):
        agents = self.agentFor(parser)
        for agent in agents:
            host, port = agent
            self.sendto(host, port, parser.msg())

    def receive(self, parser):
        self.dispatch(parser)

    def sendto(self, host, port, message, delay = True):
        try:
            self._listener.send(message, host, port)
            return True
        except Exception as e:
            return False
