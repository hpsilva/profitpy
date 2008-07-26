#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from itertools import ifilter

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QFrame, QIcon

from profit.lib import SessionHandler, nameIn
from profit.lib.gui import ValueTableItem
from profit.workbench.widgets.ui_portfoliodisplay import Ui_PortfolioDisplay


def replayPortfolio(messages, callback):
    ismsg = nameIn('UpdatePortfolio')
    symbols = (m.contract.m_symbol for t, m in messages if ismsg(m))
    for symbol in set(symbols):
        def pred((t, m)):
            return ismsg(m) and m.contract.m_symbol==symbol
        for time, message in ifilter(pred, reversed(messages)):
            callback(message)
            break


class PortfolioDisplay(QFrame, Ui_PortfolioDisplay, SessionHandler):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.portfolioItems = {}
        self.portfolioTable.verticalHeader().hide()
        self.requestSession()

    def setSession(self, session):
        self.session = session
        replayPortfolio(session.messages, self.on_session_UpdatePortfolio)
        session.registerMeta(self)

    def on_session_UpdatePortfolio(self, message):
        sym = message.contract.m_symbol
        table = self.portfolioTable
        try:
            items = self.portfolioItems[sym]
        except (KeyError, ):
            items = self.portfolioItems[sym] = table.newItemsRow()
            items[0].setSymbol(sym)
            for item in items[1:]:
                item.setValueAlign()
            table.resizeColumnToContents(0)
            table.resizeRowsToContents()
        items[1].setValue(message.position)
        items[2].setValue(message.marketPrice)
        items[3].setValue(message.marketValue)
        items[4].setValue(message.averageCost)
        items[5].setValue(message.unrealizedPNL)
        items[6].setValue(message.realizedPNL)
        items[7].setText(message.accountName)
        for col in range(table.columnCount()):
            table.resizeColumnToContents(col)

