#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>


from PyQt4.QtCore import QObject

from profit.lib import logging
from profit.lib.core import Settings


class StrategyManager(QObject):
    def __init__(self, session, parent=None):
        QObject.__init__(self, parent)
        self.session = session
        self.accountSupervisor = None
        self.orderSupervisor = None
        self.tradeIndicator = None
        self.enabled = True
        session.registerMeta(self)

    def setEnabled(self, enable=True):
        self.enabled = enabled

    def on_session_TickSize_TickPrice(self, message):
        if self.tradeIndicator:
            indication = self.tradeIndicator(message)
            if indication and self.accountSupervisor:
                order = self.accountSupervisor(indication)
                if order and self.orderSupervisor:
                    self.orderSupervisor(order)
                elif order and not self.orderSupervisor:
                    pass
                    #logging.debug(
                    #    'no order supervisor - skipped message %s', message)
            elif indication and not self.accountSupervisor:
                pass
                #logging.debug(
                #    'no account supervisor - skipped message %s', message)
        else:
            pass
            #logging.debug(
            #    'no trade indicator - skipped message %s', message)


def referenceSchema():
    """ Returns a copy of the reference strategy schema.

    """
    return [
        {'currency': '',
        'exchange': 'SMART',
        'expiry': '',
        'fields': [{'id': 2,
                  'indexes': [{'indexes': [{'indexes': [],
                                            'name': 'MedianValue-1',
                                            'parameters': {'periods': 1,
                                                           'series': ''},
                                            'typeName': 'MedianValue'},
                                           {'indexes': [],
                                            'name': 'TimeIndex-1',
                                            'parameters': {'series': ''},
                                            'typeName': 'TimeIndex'},
                                           {'indexes': [],
                                            'name': 'SMA-1',
                                            'parameters': {'periods': 1,
                                                           'series': ''},
                                            'typeName': 'SMA'}],
                               'name': 'DelayFilter-1',
                               'parameters': {'lookback': 1, 'series': ''},
                               'typeName': 'DelayFilter'},
                              {'indexes': [],
                               'name': 'KAMA-1',
                               'parameters': {'fast_look': 2.0,
                                              'periods': 1,
                                              'series': '',
                                              'slow_look': 30.0},
                               'typeName': 'KAMA'},
                              {'indexes': [],
                               'name': 'EMA-1',
                               'parameters': {'k': 2.0,
                                              'periods': 1,
                                              'series': 'askPrice'},
                               'typeName': 'EMA'}],
                  'name': 'askPrice'},
                 {'id': 1,
                  'indexes': [{'indexes': [],
                               'name': 'MACDHistogram-1',
                               'parameters': {'series': 'askPrice',
                                              'signal': 'bidPrice'},
                               'typeName': 'MACDHistogram'}],
                  'name': 'bidPrice'},
                 {'id': 4, 'indexes': [], 'name': 'lastPrice'}],
        'right': '',
        'secType': 'STK',
        'strike': 0.0,
        'symbol': 'AAPL',
        'tickerId': 100},
        {'currency': '',
        'exchange': '',
        'expiry': '',
        'fields': [{'id': 3,
                  'indexes': [{'indexes': [],
                               'name': 'BandPassFilter-1',
                               'parameters': {'hi': 0.029999999999999999,
                                              'low': 0.040000000000000001,
                                              'series': 'askSize'},
                               'typeName': 'BandPassFilter'},
                              {'indexes': [{'indexes': [{'indexes': [],
                                                         'name': 'DownMovement-1',
                                                         'parameters': {'series': 'Convergence-1'},
                                                         'typeName': 'DownMovement'}],
                                            'name': 'Convergence-1',
                                            'parameters': {'series': 'BandPassFilter-1',
                                                           'signal': 'CenterOfGravity-1'},
                                            'typeName': 'Convergence'}],
                               'name': 'BollingerBand-1',
                               'parameters': {'dev_factor': 0.050000000000000003,
                                              'period': 10,
                                              'series': 'askSize'},
                               'typeName': 'BollingerBand'},
                              {'indexes': [],
                               'name': 'CenterOfGravity-1',
                               'parameters': {'periods': 6,
                                              'series': 'askSize'},
                               'typeName': 'CenterOfGravity'}],
                  'name': 'askSize'}],
        'right': '',
        'secType': 'STK',
        'strike': 0.0,
        'symbol': 'CSCO',
        'tickerId': 101},
        {'currency': '',
        'exchange': '',
        'expiry': '',
        'fields': [],
        'right': '',
        'secType': 'STK',
        'strike': 0.0,
        'symbol': 'EBAY',
        'tickerId': 102}]
