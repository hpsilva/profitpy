#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase, Yichun Wei
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>
#         Yichun Wei <yichun.wei@gmail.com>

import sys
import os
import logging

from cPickle import PicklingError, UnpicklingError, dump, load
from itertools import ifilter
from time import time, strftime

from PyQt4.QtCore import QObject, QThread, SIGNAL

from ib.ext.Contract import Contract
from ib.ext.ExecutionFilter import ExecutionFilter
from ib.ext.Order import Order
from ib.ext.TickType import TickType

from ib.opt import ibConnection
from ib.opt.message import registry

from profit.lib.core import Signals
from profit.series import Series, MACDHistogram
try:
    from profit.series import EMA, KAMA
except (ImportError, ):
    EMA = KAMA = None
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
            acctdata = self[key]
        except (KeyError, ):
            try:
                iv = float(message.value)
            except (ValueError, ):
                pass
            else:
                acctdata = self[key] = \
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
            tickerdata = self[tickerId]
        except (KeyError, ):
            tickerdata = self[tickerId] = \
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

from Queue import Queue

class HistoricalDataCollection(QThread, DataCollection):

    # "date" has to be the 1st in the list so that data has the same length
    # this class check "date" to determine if data are finished.
    fields = [(int, "date"),
            (float, "open"),
            (float, "high"),
            (float, "low"),
            (float, "close"),
            (int,   "volume"),
            (int,   "count"),
            (float, "WAP"),
            (bool,  "hasGaps"),
            ]

    def __init__(self, session, request_queue, savedir='./histdata/'):
        QThread.__init__(self, session)
        DataCollection.__init__(self, session)
        self.idsym = {}
        self.request_queue = request_queue 
        self.savedir = savedir
        session.registerMeta(self)
        self.session = session

    def run(self):
        self.requestNext()

    def on_session_HistoricalData(self, message):
        reqId = message.reqId
        try:
            tickerdata = self.data[reqId]
        except (KeyError, ):
            tickerdata = self.data[reqId] = \
                         self.session.builder.ticker(reqId)
            self.emit(Signals.createdTicker, reqId, tickerdata)

        for format, name in self.fields:
            try:
                value = format(getattr(message, name))
            except (ValueError,):
                #if name=="date" and value.startswith("finished"):
                self.save(reqId)
                self.emit(Signals.finishedHistoricalData, reqId)
                self.requestNext()
                return
            try:
                seq = tickerdata.series[name]
            except (KeyError, ):
                seq = tickerdata.series[name] = \
                      self.session.builder.historal_series(reqId, name)
                self.emit(Signals.createdSeries, reqId, name)
            seq.append(value)

    def requestNext(self):
        sym, reqId = self.request_queue.get()
        self.requestHistoricalData(reqId, sym.upper())

    def requestHistoricalData(self, id, symbol):
        #sess = self.parent()  # not working?
        sess = self.session
        connection = sess.connection
        contract = sess.builder.contract(symbol)
        histparams = sess.builder.paramsHistoricalData()
        sess.connection.reqHistoricalData(id, contract, **histparams)
        self.idsym[id] = symbol
        self.emit(Signals.requestedHistoricalData, id, symbol)
        logging.debug("requested for (%s, %d, %r)" % (symbol, id, histparams))

    def save(self, reqId):
        data = self.data[reqId]
        symbol = self.idsym[reqId]
        fpath = os.path.join(self.savedir, symbol[0])
        try:
            os.makedirs(fpath)
        except:
            pass
        fname = os.path.join(fpath, symbol)
        dump(data, open(fname, "wb"), protocol=-1)


class SessionBuilder(object):
    default_paramsHistoricalData = {
        "endDateTime"       :   strftime("%Y%m%d %H:%M:%S PST", (2007,1,1,0,0,0,0,0,0)),
        "durationStr"       :   "6 D",
        "barSizeSetting"    :   "1 min",
        "whatToShow"        :   "TRADES",   #"BID_ASK",  # "TRADES"
        "useRTH"            :   1,          # 0 for not
        "formatDate"        :   2,          # 2 for seconds since 1970/1/1
        }

    @classmethod
    def paramsHistoricalData(cls, **kwds):
        cls.default_paramsHistoricalData.update(kwds)
        return cls.default_paramsHistoricalData 

    def accountData(self, *k):
        s = Series()
        if EMA:
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
        if EMA and KAMA:
            s.addIndex('EMA-20', EMA, s, 20)
            s.addIndex('EMA-40', EMA, s, 40)
            v = s.addIndex('KAMA-10', KAMA, s, 10)
            v.addIndex('EMA-5', EMA, v, 5)
        return s

    def historal_series(self, tickerId, field):
        s = Series()
        if field in ["date", "hasGaps"]:
            return s
        elif EMA and KAMA:
            s.addIndex('EMA-20', EMA, s, 20)
            s.addIndex('EMA-40', EMA, s, 40)
            v = s.addIndex('KAMA-10', KAMA, s, 10)
            v.addIndex('EMA-5', EMA, v, 5)
            return s


class Session(QObject):
    def __init__(self, builder=None, strategy=True):
        QObject.__init__(self)
        self.setObjectName('session')
        self.builder = builder if builder else SessionBuilder()
        self.connection = self.sessionFile = self.nextId = None
        self.messages = []
        self.savedLength = 0
        self.typedMessages = {}
        self.bareMessages = []
        self.accountCollection = ac = AccountCollection(self)
        self.tickerCollection = tc = TickerCollection(self)
        self.histdata_queue = Queue()
        self.historicalCollection = hc = HistoricalDataCollection(self, self.histdata_queue)
        if strategy:
            self.strategy = Strategy()
        connect = self.connect
        connect(
            ac, Signals.createdAccountData, self, Signals.createdAccountData)
        connect(
            tc, Signals.createdSeries, self, Signals.createdSeries)
        connect(
            tc, Signals.createdTicker, self, Signals.createdTicker)

    def __str__(self):
        return '<Session 0x%x (messages=%s connected=%s)>' % \
               (id(self), len(self.messages), self.isConnected)

    def items(self):
        return [
            ('account', ()),
            ('connection', ()),
            ('executions', ()),
            ('messages', ()),
            ('orders', ()),
            ('portfolio', ()),
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
        prefix = 'on_session_'
        names = [n for n in dir(instance) if n.startswith('on_session_')]
        for name in names:
            keys = name[len(prefix):].split('_')
            for key in keys:
                self.deregister(getattr(instance, name), key)


    def connectTWS(self, hostName, portNo, clientId, enableLogging=False):
        self.connection = con = ibConnection(hostName, portNo, clientId)
        con.enableLogging(enableLogging)
        con.connect()
        con.registerAll(self.receiveMessage)
        con.register(self.on_nextValidId, 'NextValidId')
        self.emit(Signals.connectedTWS)
        con.register(self.on_error, 'Error')
        self.historicalCollection.start()

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
        for sym, tid in self.builder.symbols().items():
            contract = self.builder.contract(sym)
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

    def requestHistoricalData(self, reqId, sym):
        self.historicalCollection.put((sym, reqId))

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
