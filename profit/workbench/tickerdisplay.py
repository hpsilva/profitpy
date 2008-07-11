#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from functools import partial
from itertools import ifilter
from string import Template

from PyQt4.QtCore import QUrl, QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QAction, QApplication, QFrame, QIcon, QMenu

from ib.ext.TickType import TickType
from ib.opt.message import TickPrice

from profit.lib import defaults
from profit.lib.core import SessionHandler, Settings, Signals, nameIn
from profit.lib.gui import UrlAction, UrlRequestor, ValueTableItem, separator as sep
from profit.workbench.portfoliodisplay import replayPortfolio
from profit.workbench.widgets.ui_tickerdisplay import Ui_TickerDisplay


fieldColumns = {
    TickType.ASK_SIZE : 3,
    TickType.ASK : 4,
    TickType.BID_SIZE : 5,
    TickType.BID : 6,
    TickType.LAST_SIZE : 7,
    TickType.LAST : 8,
    }


def replayTick(messages, symbols, callback):
    isMsg = nameIn('TickSize', 'TickPrice')
    for symbol, tickerId in symbols.items():
        for field in fieldColumns.keys():
            def pred((t, m)):
                return isMsg(m) and m.field==field and m.tickerId==tickerId
            for time, message in ifilter(pred, reversed(messages)):
                callback(message)
                break


def fakeTickerMessages(symbol, tickerId):
    for field in fieldColumns:
        yield TickPrice(tickerId=tickerId, field=field, price=0, canAutoExecute=False)


class TickerDisplay(QFrame, Ui_TickerDisplay, SessionHandler, UrlRequestor):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.symbols = {}
        self.tickerItems = {}
        self.settings = Settings()
        self.tickerTable.verticalHeader().hide()
        self.contextActions = [sep(), self.actionChart, self.actionOrder, sep(), ]
        app = QApplication.instance()
        self.connect(self, Signals.openUrl, app, Signals.openUrl)
        self.requestSession()

    def setSession(self, session):
        self.session = session
        symbols = self.symbols
        symbols.update(session.strategy.symbols())
        replayTick(session.messages, symbols,
                   self.on_session_TickPrice_TickSize)
        replayPortfolio(session.messages, self.on_session_UpdatePortfolio)
        session.registerMeta(self)
        if not session.messages:
            for symbol, tickerId in symbols.items():
                for msg in fakeTickerMessages(symbol, tickerId):
                    self.on_session_TickPrice_TickSize(msg)

    @pyqtSignature('')
    def on_actionChart_triggered(self):
        table = self.tickerTable
        try:
            item = table.selectedItems()[0]
        except (IndexError, ):
            pass
        else:
            index = table.model().index(item.row(), 0)
            if index and index.isValid():
                self.emit(Signals.tickerClicked, table.itemFromIndex(index))

    @pyqtSignature('')
    def on_actionOrder_triggered(self):
        print '## order for ', self.actionOrder.data().toString()

    @pyqtSignature('')
    def on_closePosition(self):
        print '## close position order dialog'

    def menuActions(self, index):
        data = index.data()
        symbol = data.toString()
        icon = QIcon(index.data(Qt.DecorationRole))
        actions = [QAction(icon, symbol, None), ]
        actions.extend(self.contextActions)
        for act in actions:
            act.setData(data)
        return actions

    def urlActions(self, symbol):
        actions = []
        settings = self.settings
        settings.beginGroup(self.settings.keys.urls)
        urls = settings.value(settings.keys.tickerurls, defaults.tickerUrls())
        settings.endGroup()
        ## print [str(s) for s in urls.toStringList()] # wtf
        urls = [str(s) for s in defaults.tickerUrls()]
        for url in urls: #urls.toStringList(): # wtf
            try:
                name, url = str(url).split(':', 1)
                url = Template(url).substitute(symbol=symbol)
            except (KeyError, ValueError, ):
                continue
            act = UrlAction(name+'...', url, '%s %s' % (symbol, name))
            self.connect(act, Signals.triggered, partial(self.on_urlAction, action=act))
            actions.append(act)
        return actions

    def closePositionAction(self, row):
        act = None
        index = self.tickerTable.model().index(row, 1)
        if index and index.isValid():
            try:
                pos = float(index.data().toString())
            except (ValueError, ):
                pos = 0
            if pos:
                act = QAction('Close %s shares...' % abs(pos), None)
                self.connect(act, Signals.triggered, self.on_closePosition)
        return act

    def on_tickerTable_customContextMenuRequested(self, pos):
        table = self.tickerTable
        item = table.itemAt(pos)
        if item:
            row = item.row()
            index = table.model().index(row, 0)
            if index and index.isValid():
                actions = self.menuActions(index)
                close = self.closePositionAction(row)
                if close:
                    actions.insert(-1, close)
                actions.extend(self.urlActions(index.data().toString()))
                QMenu.exec_(actions, table.viewport().mapToGlobal(pos))

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
