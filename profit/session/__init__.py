#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

import sys

from cPickle import PicklingError, UnpicklingError, dump, load
from itertools import ifilter
from time import time

from PyQt4.QtCore import QObject, SIGNAL

from ib.ext.Contract import Contract
from ib.ext.ExecutionFilter import ExecutionFilter
from ib.ext.Order import Order
from ib.ext.TickType import TickType

from ib.opt import ibConnection
from ib.opt.message import registry

from profit.lib import Signals


class Index(list):
    def __init__(self, name):
        list.__init__(self)
        self.name = name


class Series(list):
    def __init__(self):
        list.__init__(self)
        self.indexes = [
            Index('MACD'),
            Index('EMA-20'),
            Index('SMA-50'),
            Index('KAMA'),
        ]

    def append(self, value):
        list.append(self, value)
        for index in self.indexes:
            index.append(value)


class Ticker(object):
    def __init__(self):
        self.series = {}


class TickerCollection(QObject):
    """

    """
    def __init__(self, session):
        QObject.__init__(self)
        self.tickers = {}
        for tid in session.builder.symbols().values():
            self[tid] = self.newTicker()
        session.registerMeta(self)

    def __getitem__(self, name):
        return self.tickers[name]

    def __setitem__(self, name, value):
        self.tickers[name] = value

    @classmethod
    def newTicker(cls):
        return Ticker()

    def on_session_TickPrice_TickSize(self, message):
        tickerId = message.tickerId
        field = message.field
        try:
            tickerdata = self.tickers[tickerId]
        except (KeyError, ):
            tickerdata = self.tickers[tickerId] = self.newTicker()
            self.emit(Signals.createdTicker, tickerId, tickerdata)
        try:
            value = message.price
        except (AttributeError, ):
            value = message.size
        try:
            seq = tickerdata.series[field]
        except (KeyError, ):
            seq = tickerdata.series[field] = Series()
            self.emit(Signals.createdSeries, tickerId, field)
        seq.append(value)


class SessionBuilder(object):
    def strategy(self):
        return None

    def symbols(self):
        return {'AAPL':100, 'EBAY':101, 'NVDA':102}

    def contract(self, symbol, secType='STK', exchange='SMART',
                 currency='USD'):
        contract = Contract()
        contract.m_symbol = symbol
        contract.m_secType = secType
        contract.m_exchange = exchange
        contract.m_currency = currency
        return contract

    def order(self):
        return Order()


class Session(QObject):
    def __init__(self, data=None, builder=None):
        QObject.__init__(self)
        self.setObjectName('session')
        self.data = data if data else {}
        self.builder = builder if builder else SessionBuilder()
        self.connection = None
        self.messages = []
        self.savedLength = 0
        self.filename = None
        self.nextId = None
        self.typedMessages = {}
        self.bareMessages = []
        self.tickerCollection = tickerCollection = TickerCollection(self)
        self.connect(tickerCollection, Signals.createdTicker,
                     self, Signals.createdTicker)
        self.connect(tickerCollection, Signals.createdSeries,
                     self, Signals.createdSeries)

    def items(self):
        return [
            ('account', ()),
            ('connection', ()),
            ('executions', ()),
            ('messages', ()),
            ('orders', ()),
            ('portfolio', ()),
            ('strategy', ()),
            ('tickers', self.builder.symbols()),
            ]

    def disconnectTWS(self):
        if self.isConnected:
            self.connection.disconnect()
            self.emit(Signals.disconnectedTWS)

    @property
    def isConnected(self):
        return bool(self.connection and self.connection.isConnected())

    @property
    def isModified(self):
        return len(self.messages) != self.savedLength

    def register(self, obj, name, other=None):
        if other is None:
            self.connect(self, SIGNAL(name), obj)
        else:
            self.connect(self, SIGNAL(name), obj, other)

    def registerAll(self, obj, other=None):
        names = [typ.__name__ for typ in registry.values()]
        for name in names:
            if other is None:
                self.connect(self, SIGNAL(name), obj)
            else:
                self.connect(self, SIGNAL(name), obj, other)

    def registerMeta(self, instance):
        prefix = 'on_session_'
        names = [n for n in dir(instance) if n.startswith('on_session_')]
        for name in names:
            keys = name[len(prefix):].split('_')
            for key in keys:
                self.register(getattr(instance, name), key)

    def deregister(self, obj, name, other=None):
        if other is None:
            self.disconnect(self, SIGNAL(name), obj)
        else:
            self.disconnect(self, SIGNAL(name), obj, other)

    def deregisterAll(self, obj, other=None):
        names = [typ.__name__ for typ in registry.values()]
        for name in names:
            if other is None:
                self.disconnect(self, SIGNAL(name), obj)
            else:
                self.disconnect(self, SIGNAL(name), obj, other)

    def deregisterMeta(self, instance):
        raise NotImplementedError()

    def connectTWS(self, hostName, portNo, clientId, enableLogging=False):
        self.connection = con = ibConnection(hostName, portNo, clientId)
        con.enableLogging(enableLogging)
        con.connect()
        con.registerAll(self.receiveMessage)
        con.register(self.on_nextValidId, 'NextValidId')
        self.emit(Signals.connectedTWS)

    def on_nextValidId(self, message):
        self.nextId = int(message.orderId)

    def receiveMessage(self, message, timefunc=time):
        messages = self.messages
        current = (timefunc(), message)
        messages.append(current)
        typename = message.typeName
        typed = self.typedMessages.setdefault(typename, [])
        typed.append(current + (len(messages), ))
        self.bareMessages.append(message)
        self.emit(SIGNAL(typename), message)

    def requestTickers(self):
        connection = self.connection
        for sym, tid in self.builder.symbols().items():
            contract = self.builder.contract(sym)
            connection.reqMktData(tid, contract, '')
            connection.reqMktDepth(tid, contract, 1)

    def requestAccount(self):
        self.connection.reqAccountUpdates(True, "")

    def requestOrders(self):
        connection = self.connection
        filt = ExecutionFilter()
        connection.reqExecutions(filt)
        connection.reqAllOpenOrders()
        connection.reqOpenOrders()

        contract = self.builder.contract('ASDF', secType='ASDF')
        connection.reqMktData(1, contract, '')
        return

    def testContract(self, symbol='AAPL'):
        orderid = self.nextId

        if orderid is None:
            return False

        contract = self.builder.contract(symbol)
        order = self.builder.order()
        order.m_action = 'SELL'
        order.m_orderType = 'MKT'
        order.m_totalQuantity = '300'
        order.m_lmtPrice = contract.m_auxPrice = 78.5
        order.m_openClose = 'O'
        self.connection.placeOrder(orderid, contract, order)
        self.nextId += 1
        return True

    def save(self):
        status = False
        try:
            handle = open(self.filename, 'wb')
        except (IOError, ):
            pass
        else:
            last = len(self.messages)
            messages = self.messages[0:last]
            try:
                dump(messages, handle, protocol=-1)
                self.savedLength = last
                status = True
            except (PicklingError, ):
                pass
            finally:
                handle.close()
        return status

    def load(self, filename):
        """ Restores session messages from file.

        This function first yields the total number of messages
        loaded, then yields the index of each message after it has
        pumped the message thru the receiveMessage function.  This
        oddness is used to support the QProgressDialog used in the
        main window during session loading.

        @param filename name of file from which to read messages.
        @return None
        """
        try:
            handle = open(filename, 'rb')
        except (IOError, ):
            pass
        else:
            try:
                messages = load(handle)
                yield len(messages)
                for index, (mtime, message) in enumerate(messages):
                    self.receiveMessage(message, lambda:mtime)
                    yield index
            except (UnpicklingError, ):
                pass
            finally:
                self.filename = filename
                self.savedLength = len(messages)
                handle.close()

