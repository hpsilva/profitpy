#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase, Yichun Wei
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>
#         Yichun Wei <yichun.wei@gmail.com>

import os
import logging

from cPickle import PicklingError, UnpicklingError, dump, load
from itertools import ifilter
from random import randint
from time import time, strftime
from Queue import Queue

from PyQt4.QtCore import QObject, QMutex, QThread, SIGNAL

from ib.ext.Contract import Contract
from ib.ext.ExecutionFilter import ExecutionFilter
from ib.ext.Order import Order
from ib.ext.TickType import TickType
from ib.opt import ibConnection
from ib.opt.message import registry

from profit.lib.core import Signals
from profit.lib.series import Series, MACDHistogram
from profit.lib.session.collection import (AccountCollection,
                                           TickerCollection,
                                           HistoricalDataCollection, )
from profit.lib.session.savethread import SaveThread
try:
    from profit.lib.series import EMA, KAMA
except (ImportError, ):
    EMA = KAMA = None

from profit.lib.strategy.builder import SessionStrategyBuilder



class Session(QObject):
    """ This is the big-honkin Session class.

    """
    def __init__(self, strategy=None):
        QObject.__init__(self)
        self.setObjectName('session')
        self.strategy = strategy if strategy else SessionStrategyBuilder()
        self.connection = self.sessionFile = self.nextId = None
        self.messages = []
        self.bareMessages = []
        self.savedLength = 0
        self.typedMessages = {}
        self.accountCollection = ac = AccountCollection(self)
        self.tickerCollection = tc = TickerCollection(self)
        self.historicalDataCollection = hc = HistoricalDataCollection(self)
        connect = self.connect
        connect(ac, Signals.createdAccountData, self, Signals.createdAccountData)
        connect(tc, Signals.createdSeries, self, Signals.createdSeries)
        connect(tc, Signals.createdTicker, self, Signals.createdTicker)
        connect(hc, Signals.historicalDataStart,
                self, Signals.historicalDataStart)
        connect(hc, Signals.historicalDataFinish,
                self, Signals.historicalDataFinish)

    def __str__(self):
        fmt = '<Session 0x%x messages:%s connected:%s>'
        args = id(self), len(self.messages), int(self.isConnected)
        return  fmt % args

    def items(self):
        return [
            ('account', ()),
            ('connection', ()),
            ('executions', ()),
            ('historical data', ()),
            ('messages', ()),
            ('orders', ()),
            ('portfolio', ()),
            ('strategy', ()),
            ('tickers', self.strategy.symbols()),
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
        prefix = 'on_session_'
        names = [n for n in dir(instance) if n.startswith('on_session_')]
        for name in names:
            keys = name[len(prefix):].split('_')
            for key in keys:
                self.deregister(getattr(instance, name), key)

    def connectTWS(self, hostName, portNo, clientId, enableLogging=False):
        if clientId == -1:
            clientId = randint(100, 999)
        if portNo == 1023:
            portNo = 7496
        self.connection = con = ibConnection(hostName, portNo, clientId)
        con.enableLogging(enableLogging)
        con.connect()
        con.registerAll(self.receiveMessage)
        con.register(self.on_nextValidId, 'NextValidId')
        self.emit(Signals.connectedTWS)
        con.register(self.on_error, 'Error')

    def on_nextValidId(self, message):
        self.nextId = int(message.orderId)

    def on_error(self, message):
        logging.debug(str(message))

    def receiveMessage(self, message, mtime=time):
        messages = self.messages
        try:
            mtime = mtime()
        except (TypeError, ):
            pass
        current = (mtime, message)
        messages.append(current)
        typename = message.typeName
        typed = self.typedMessages.setdefault(typename, [])
        typed.append(current + (len(messages), ))
        self.bareMessages.append(message)
        self.emit(SIGNAL(typename), message)

    def requestTickers(self):
        connection = self.connection
        ## need to make this lazy
        for sym, tid in self.strategy.symbols().items():
            contract = self.strategy.contract(sym)
            connection.reqMktData(tid, contract, '', False)
            connection.reqMktDepth(tid, contract, 1)

    def requestAccount(self):
        self.connection.reqAccountUpdates(True, "")

    def requestOrders(self):
        connection = self.connection
        filt = ExecutionFilter()
        connection.reqExecutions(filt)
        connection.reqAllOpenOrders()
        connection.reqOpenOrders()

    def requestHistoricalData(self, params):
        ## we should msg the object instead
        self.historicalDataCollection.begin(params)

    def testContract(self, symbol='AAPL'):
        orderid = self.nextId
        if orderid is None:
            return False
        contract = self.strategy.contract(symbol)
        order = self.strategy.order()
        order.m_action = 'SELL'
        order.m_orderType = 'MKT'
        order.m_totalQuantity = '300'
        order.m_lmtPrice = contract.m_auxPrice = 78.5
        order.m_openClose = 'O'
        self.connection.placeOrder(orderid, contract, order)
        self.nextId += 1
        return True

    def saveFinished(self):
        if self.saveThread.status:
            count = self.saveThread.writeCount
            self.savedLength = count
            msg = 'Session file saved.  Wrote %s messages.' % count
        else:
            msg = 'Error saving file.'
        self.emit(Signals.sessionStatus, msg)

    def exportFinished(self):
        if self.exportThread.status:
            count = self.exportThread.writeCount
            msg = 'Session exported.  Wrote %s messages.' % count
        else:
            msg = 'Error exporting messages.'
        self.emit(Signals.sessionStatus, msg)

    def saveTerminated(self):
        self.emit(Signals.sessionStatus, 'Session file save terminated.')

    def exportTerminated(self):
        self.emit(Signals.sessionStatus, 'Session export terminated.')

    @property
    def saveInProgress(self):
        try:
            thread = self.saveThread
        except (AttributeError, ):
            return False
        else:
            return thread.isRunning()

    def save(self):
        if self.saveInProgress:
            return
        self.saveThread = thread = \
            SaveThread(filename=self.sessionFile, types=None, parent=self)
        self.connect(thread, Signals.finished, self.saveFinished)
        self.connect(thread, Signals.terminated, self.saveTerminated)
        thread.start()
        self.emit(Signals.sessionStatus, 'Started session file save.')

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
                    self.receiveMessage(message, mtime)
                    yield index
            except (UnpicklingError, ):
                pass
            finally:
                self.sessionFile= filename
                self.savedLength = len(messages)
                handle.close()

    def importMessages(self, filename, types):
        """ Import messages directly into this session instance.

        This function is a generator; it first yields the total number
        of messages it has imported, then yields the message's index.
        Prior to yielding the message index, the message object is
        sent thru the Qt signal plumbing.

        @param filename name of serialized messages file
        @param types sequence or set of types to import
        @return None
        """
        try:
            handle = open(filename, 'rb')
        except (IOError, ):
            pass
        else:
            def messageFilter((mtime, message)):
                return message.typeName in types
            try:
                messages = filter(messageFilter, load(handle))
                def importer():
                    yield len(messages)
                    for index, (mtime, message) in enumerate(messages):
                        self.receiveMessage(message, mtime)
                        yield index
                return importer
            except (UnpicklingError, ):
                pass
            finally:
                handle.close()

    @property
    def exportInProgress(self):
        try:
            thread = self.exportThread
        except (AttributeError, ):
            return False
        else:
            return thread.isRunning()

    def exportMessages(self, filename, types):
        if self.exportInProgress:
            return
        self.exportThread = thread = \
            SaveThread(filename=filename, types=types, parent=self)
        self.connect(thread, Signals.finished, self.exportFinished)
        self.connect(thread, Signals.terminated, self.exportTerminated)
        thread.start()
        self.emit(Signals.sessionStatus, 'Started session export.')
