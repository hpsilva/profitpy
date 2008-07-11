#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase, Yichun Wei
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>
#         Yichun Wei <yichun.wei@gmail.com>

from time import time, strftime
from profit.lib.series import Series, MACDHistogram

from ib.ext.Contract import Contract
from ib.ext.ExecutionFilter import ExecutionFilter
from ib.ext.Order import Order
from ib.ext.TickType import TickType
from ib.opt import ibConnection
from ib.opt.message import registry

from profit.lib.strategy import Strategy as StrategyLoader
try:
    from profit.lib.series import EMA, KAMA
except (ImportError, ):
    EMA = KAMA = None


class StrategyBuilderTicker(object):
    def __init__(self):
        self.series = {}


class SessionStrategyBuilder(object):
    default_paramsHistoricalData = {
        ## change to use datetime
        "endDateTime"       :   strftime("%Y%m%d %H:%M:%S PST", (2007,1,1,0,0,0,0,0,0)),
        "durationStr"       :   "6 D",
        "barSizeSetting"    :   "1 min",
        "whatToShow"        :   "TRADES",   #"BID_ASK",  # "TRADES"
        "useRTH"            :   1,          # 0 for not
        "formatDate"        :   2,          # 2 for seconds since 1970/1/1
        }

    def __init__(self):
        self.loader = StrategyLoader()

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
        return StrategyBuilderTicker()

    def series(self, tickerId, field):
        s = Series()
        if EMA and KAMA:
            s.addIndex('EMA-20', EMA, s, 20)
            s.addIndex('EMA-40', EMA, s, 40)
            v = s.addIndex('KAMA-10', KAMA, s, 10)
            v.addIndex('EMA-5', EMA, v, 5)
        return s

    def historicalSeries(self, tickerId, field):
        s = Series()
        if field in ['date', 'hasGaps']:
            return s
        elif EMA and KAMA:
            s.addIndex('EMA-20', EMA, s, 20)
            s.addIndex('EMA-40', EMA, s, 40)
            v = s.addIndex('KAMA-10', KAMA, s, 10)
            v.addIndex('EMA-5', EMA, v, 5)
            return s
