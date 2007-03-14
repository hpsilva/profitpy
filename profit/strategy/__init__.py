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
