#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

import sys

from cPickle import PicklingError, UnpicklingError, dump, load
from itertools import ifilter
from time import time

from PyQt4.QtCore import QObject, QThread, SIGNAL

from ib.ext.Contract import Contract
from ib.ext.ExecutionFilter import ExecutionFilter
from ib.ext.Order import Order
from ib.ext.TickType import TickType

from ib.opt import ibConnection
from ib.opt.message import registry

from profit.lib.core import Signals
from profit.series import Series, MACDHistogram, EMA, KAMA
from profit.strategy import Strategy

class Ticker(object):
    def __init__(self):
        self.series = {}


class DataCollection(QObject):
    def __init__(self, session):
        QObject.__init__(self)
        self.session = session
        self.data = {}

    def __contains__(self, item):
        return item in self.data

    def __getitem__(self, name):
        return self.data[name]

    def __setitem__(self, name, value):
        self.data[name] = value


class AccountCollection(DataCollection):
    def __init__(self, session):
        DataCollection.__init__(self, session)
        self.last = {}
        session.registerMeta(self)

    def on_session_UpdateAccountValue(self, message):
        key = (message.key, message.currency, message.accountName)
        try:
            acctdata = self.data[key]
        except (KeyError, ):
            try:
                iv = float(message.value)
            except (ValueError, ):
                pass
            else:
                acctdata = self.data[key] = \
                           self.session.builder.accountData(key)
                self.emit(Signals.createdAccountData, key, acctdata, iv)
        try:
            v = float(message.value)
        except (ValueError, ):
            v = message.value
        else:
            acctdata.append(v)
        self.last[key] = v


class TickerCollection(DataCollection):
    def __init__(self, session):
        DataCollection.__init__(self, session)
        for tid in session.builder.symbols().values():
            self[tid] = session.builder.ticker(tid)
        session.registerMeta(self)

    def on_session_TickPrice_TickSize(self, message):
        tickerId = message.tickerId
        try:
            tickerdata = self.data[tickerId]
        except (KeyError, ):
            tickerdata = self.data[tickerId] = \
                         self.session.builder.ticker(tickerId)
            self.emit(Signals.createdTicker, tickerId, tickerdata)
        try:
            value = message.price
        except (AttributeError, ):
            value = message.size
        field = message.field
        try:
            seq = tickerdata.series[field]
        except (KeyError, ):
            seq = tickerdata.series[field] = \
                  self.session.builder.series(tickerId, field)
            self.emit(Signals.createdSeries, tickerId, field)
        seq.append(value)


class SessionBuilder(object):
    def accountData(self, *k):
        s = Series()
        s.addIndex('EMA-25', EMA, s, 25)
        return s

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

    def ticker(self, tickerId):
        return Ticker()

    def series(self, tickerId, field):
        s = Series()
        s.addIndex('EMA-20', EMA, s, 20)
        s.addIndex('EMA-40', EMA, s, 40)
        s.addIndex('KAMA-10', KAMA, s, 10)
        return s


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
        self.accountCollection = AccountCollection(self)
        self.tickerCollection = TickerCollection(self)
        self.strategy = Strategy(self)
        self.connect(
            self.accountCollection, Signals.createdAccountData,
            self, Signals.createdAccountData)
        self.connect(
            self.tickerCollection, Signals.createdTicker,
            self, Signals.createdTicker)
        self.connect(
            self.tickerCollection, Signals.createdSeries,
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

    def saveFinished(self):
        if self.saveThread.status:
            count = self.saveThread.writeCount
            self.savedLength = count
            msg = 'Session file saved.  Wrote %s messages.' % count
        else:
            msg = 'Error saving file.'
        self.emit(Signals.statusMessage, msg)

    def exportFinished(self):
        if self.exportThread.status:
            count = self.exportThread.writeCount
            msg = 'Session exported.  Wrote %s messages.' % count
        else:
            msg = 'Error exporting messages.'
        self.emit(Signals.statusMessage, msg)

    def saveTerminated(self):
        self.emit(Signals.statusMessage, 'Session file save terminated.')

    def exportTerminated(self):
        self.emit(Signals.statusMessage, 'Session export terminated.')

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
            SaveThread(filename=self.filename, types=None, parent=self)
        self.connect(thread, Signals.finished, self.saveFinished)
        self.connect(thread, Signals.terminated, self.saveTerminated)
        thread.start()
        self.emit(Signals.statusMessage, 'Started session file save.')

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

    def importMessages(self, filename, types):
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
                        self.receiveMessage(message, lambda:mtime)
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
        self.emit(Signals.statusMessage, 'Started session export.')


class SaveThread(QThread):
    def __init__(self, filename, types, parent):
        QThread.__init__(self, parent)
        self.filename = filename
        self.types = types

    def run(self):
        status = False
        session = self.parent()
        try:
            handle = open(self.filename, 'wb')
        except (IOError, ):
            pass
        else:
            last = len(session.messages)
            messages = session.messages[0:last]
            types = self.types
            if types:
                def messageFilter((mtime, message)):
                    return message.typeName in types
                messages = filter(messageFilter, messages)
                last = len(messages)
            try:
                dump(messages, handle, protocol=-1)
                self.writeCount = last
                status = True
            except (PicklingError, ):
                pass
            finally:
                handle.close()
        self.status = status
