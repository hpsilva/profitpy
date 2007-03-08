#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from itertools import ifilter

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QFrame, QIcon

from ib.ext.TickType import TickType

from profit.lib.core import Signals, disabledUpdates, nameIn
from profit.lib.gui import ValueTableItem
from profit.widgets.portfoliodisplay import replayPortfolio
from profit.widgets.ui_tickerdisplay import Ui_TickerDisplay


fieldColumns = {
    TickType.ASK_SIZE : 3,
    TickType.ASK : 4,
    TickType.BID_SIZE : 5,
    TickType.BID : 6,
    TickType.LAST_SIZE : 7,
    TickType.LAST : 8,
    }


def replayTick(messages, symbols, callback):
    ismsg = nameIn('TickSize', 'TickPrice')
    for symbol, tickerId in symbols.items():
        for field in fieldColumns.keys():
            def pred((t, m)):
                return ismsg(m) and m.field==field and m.tickerId==tickerId
            for time, message in ifilter(pred, reversed(messages)):
                callback(message)
                break


class TickerDisplay(QFrame, Ui_TickerDisplay):
    def __init__(self, session, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.tickerItems = {}
        self.symbols = symbols = session.builder.symbols()
        self.tickerTable.verticalHeader().hide()
        replayTick(session.messages, symbols,
                   self.on_session_TickPrice_TickSize)
        replayPortfolio(session.messages, self.on_session_UpdatePortfolio)
        session.registerMeta(self)

    def on_tickerTable_doubleClicked(self, index):
        if not index.isValid():
            return
        col = index.column()
        row = index.row()
        item = self.tickerTable.item(row, 0)
        if (0 <= col <= 2):
            self.emit(Signals.tickerClicked, item)
        elif  (2 < col < 9):
            self.emit(Signals.tickerClicked, item, col)

    @disabledUpdates('tickerTable')
    def on_session_UpdatePortfolio(self, message):
        sym = message.contract.m_symbol
        try:
            tid = self.symbols[sym]
            items = self.tickerItems[tid]
        except (KeyError, ):
            pass
        else:
            items[1].setValue(message.position)
            items[2].setValue(message.marketValue)

    @disabledUpdates('tickerTable')
    def on_session_TickPrice_TickSize(self, message):
        tid = message.tickerId
        table = self.tickerTable
        try:
            value = message.price
        except (AttributeError, ):
            value = message.size
        try:
            items = self.tickerItems[tid]
        except (KeyError, ):
            items = self.tickerItems[tid] = table.newItemsRow()
            sym = dict([(b, a) for a, b in self.symbols.items()])[tid]
            items[0].setSymbol(sym)
            items[0].tickerId = tid
            for item in items[1:]:
                item.setValueAlign()
            table.sortItems(0)
            table.resizeColumnsToContents()
            table.resizeRowsToContents()
        try:
            index = fieldColumns[message.field]
        except (KeyError, ):
            pass
        else:
            items[index].setValue(value)
            #table.resizeColumnToContents(index)
