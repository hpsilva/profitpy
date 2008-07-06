#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase, Yichun Wei
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>
#         Yichun Wei <yichun.wei@gmail.com>
import os
import logging
from cPickle import PicklingError, UnpicklingError, dump, load

from PyQt4.QtCore import QObject, QThread
from profit.lib.core import Signals


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
                           self.session.strategy.accountData(key)
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
        for tid in session.strategy.symbols().values():
            self[tid] = session.strategy.ticker(tid)
        session.registerMeta(self)

    def on_session_TickPrice_TickSize(self, message):
        tickerId = message.tickerId
        try:
            tickerdata = self[tickerId]
        except (KeyError, ):
            tickerdata = self[tickerId] = \
                         self.session.strategy.ticker(tickerId)
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
                  self.session.strategy.series(tickerId, field)
            self.emit(Signals.createdSeries, tickerId, field)
        seq.append(value)


class HistoricalDataCollection(QThread, DataCollection):
    # "date" has to be the 1st in the list so that data has the same length
    # this class check "date" to determine if data are finished.
    fields = [
        (int, "date"),
        (float, "open"),
        (float, "high"),
        (float, "low"),
        (float, "close"),
        (int,   "volume"),
        (int,   "count"),
        (float, "WAP"),
        (bool,  "hasGaps"),
    ]

    def __init__(self, session, requestQueue, savedir='./histdata/'):
        QThread.__init__(self, session)
        DataCollection.__init__(self, session)
        self.idsym = {}
        self.requestQueue = requestQueue
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
                         self.session.strategy.ticker(reqId)
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
                      self.session.strategy.historal_series(reqId, name)
                self.emit(Signals.createdSeries, reqId, name)
            seq.append(value)

    def requestNext(self):
        sym, reqId = self.requestQueue.get()
        self.requestHistoricalData(reqId, sym.upper())

    def requestHistoricalData(self, id, symbol):
        #sess = self.parent()  # not working?
        sess = self.session
        connection = sess.connection
        contract = sess.strategy.contract(symbol)
        histparams = sess.strategy.paramsHistoricalData()
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

