#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from functools import partial
from itertools import ifilter
from string import Template

from PyQt4.QtCore import QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QAction, QFrame, QIcon, QMenu

from ib.ext.TickType import TickType
from ib.opt.message import TickPrice

from profit.lib import defaults
from profit.lib.core import (SessionHandler, SettingsHandler, Signals,
                             nameIn, DataRoles, instance)
from profit.lib.gui import (UrlRequestor, ValueTableItem, separator,
                            makeUrlAction, )
from profit.workbench.portfoliodisplay import replayPortfolio
from profit.workbench.widgets.ui_tickerdisplay import Ui_TickerDisplay


##
# Maps ticktype fields to column numbers
fieldColumns = {
    TickType.ASK_SIZE : 3,
    TickType.ASK : 4,
    TickType.BID_SIZE : 5,
    TickType.BID : 6,
    TickType.LAST_SIZE : 7,
    TickType.LAST : 8,
    }


def replayTick(messages, symbols, callback):
    """ Sends callback last message for every symbol and field

    @param messages session message sequence
    @param symbols mapping of symbol:tickerIds
    @param callback function to call with replayed messages
    @return None
    """
    isMsg = nameIn('TickSize', 'TickPrice')
    for symbol, tickerId in symbols.items():
        for field in fieldColumns.keys():
            def pred((t, m)):
                return isMsg(m) and m.field==field and m.tickerId==tickerId
            for time, message in ifilter(pred, reversed(messages)):
                callback(message)
                break


def fakeTickerMessages(tickerId):
    """ Generates fake TickPrice messages for every ticker field

    @param tickerId ticker id
    @return None
    """
    for field in fieldColumns:
        yield TickPrice(tickerId=tickerId, field=field, price=0,
                        canAutoExecute=False)


class TickerDisplay(QFrame, Ui_TickerDisplay, SessionHandler,
                    SettingsHandler, UrlRequestor):
    """

    """
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.tickerItems = {}
        self.tickerTable.verticalHeader().hide()
        app = instance()
        connect = self.connect
        connect(self, Signals.openUrl, app, Signals.openUrl)
        connect(self, Signals.tickerClicked, app, Signals.tickerClicked)
        self.requestSession()

    def setSession(self, session):
        self.session = session
        symbols = session.strategy.symbols()
        replayTick(session.messages, symbols,
                   self.on_session_TickPrice_TickSize)
        replayPortfolio(session.messages, self.on_session_UpdatePortfolio)
        session.registerMeta(self)
        if not session.messages:
            for tickerId in symbols.values():
                for msg in fakeTickerMessages(tickerId):
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

    def basicActions(self, index):
        data = index.data()
        symbol = data.toString()
        icon = QIcon(index.data(Qt.DecorationRole))
        actions = [
            QAction(icon, symbol, None),
            separator(),
            self.actionChart,
            self.actionOrder,
            separator(),
        ]
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
            act = makeUrlAction(name, url, toolTip='%s %s' % (symbol, name))
            self.connect(act, Signals.triggered, partial(self.requestUrl, action=act))
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
                actions = self.basicActions(index)
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
        sym = str(index.data().toString())
        symbols = self.session.strategy.symbols()
        try:
            tid = symbols[sym]
        except (KeyError, ):
            pass
        else:
            item.setData(DataRoles.tickerId, QVariant(tid), )
            item.setData(DataRoles.tickerSymbol, QVariant(sym))
            if (0 <= col <= 2):
                self.emit(Signals.tickerClicked, item)
            elif  (2 < col < 9):
                self.emit(Signals.tickerClicked, item, col)

    def on_session_UpdatePortfolio(self, message):
        sym = message.contract.m_symbol
        symbols = self.session.strategy.symbols()
        try:
            tid = symbols[sym]
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
            symbols = self.session.strategy.symbols()
            sym = dict([(b, a) for a, b in symbols.items()])[tid]
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
