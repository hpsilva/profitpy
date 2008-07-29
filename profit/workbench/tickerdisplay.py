#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

# TODO: cache previous values on column drop and reuse on add.
# TODO: support id, symbol, position and value fields

from functools import partial
from itertools import ifilter
from string import Template

from PyQt4.QtCore import QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QAction, QFrame, QIcon, QMenu

from ib.opt.message import TickPrice

from profit.lib import (BasicHandler, DataRoles, Signals, defaults,
                        instance, makeCheckNames, )

from profit.lib.gui import (UrlRequestor, ValueTableItem, separator,
                            makeUrlAction, )

from profit.lib.widgets.tickfieldselect import (fieldIds, itemTickField,
                                                setItemTickField, )

from profit.workbench.portfoliodisplay import replayPortfolio
from profit.workbench.widgets.ui_tickerdisplay import Ui_TickerDisplay


def replayTickerMessages(messages, symbols, callback):
    """ Invokes callback with the last message for every symbol and field

    @param messages session message sequence
    @param symbols mapping of symbol:tickerIds
    @param callback function to call with replayed messages
    @return None
    """
    isMsg = makeCheckNames('TickSize', 'TickPrice')
    for symbol, tickerId in symbols.items():
        for field in fieldIds():
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
    tick = partial(TickPrice, tickerId=tickerId, price=0, canAutoExecute=False)
    for field in fieldIds():
        yield tick(field=field)


class TickerDisplay(QFrame, Ui_TickerDisplay, BasicHandler, UrlRequestor):
    """ TickerDisplay -> shows ticker data in a nice table.

    """
    def __init__(self, parent=None):
        """ Initializer.

        @param parent ancestor of this object
        @return None
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.headerItemColumnMap = {}
        self.tickerIds = {}
        self.setupWidgets()
        self.requestSession()

    def setupWidgets(self):
        """ Make our widgets like we like.

        """
        settings = self.settings
        settings.beginGroup(self.__class__.__name__)
        defaultFields = defaults.tickerDisplayFields()
        userFields = settings.valueLoad('selectedFields', defaultFields)
        self.tickFieldSelect.setCheckedFields(userFields)
        defaultState = defaults.rightMainSplitterState()
        splitState = settings.value(settings.keys.splitstate, defaultState)
        self.splitter.restoreState(splitState.toByteArray())
        settings.endGroup()
        app = instance()
        connect = self.connect
        connect(self, Signals.openUrl, app, Signals.openUrl)
        connect(self, Signals.tickerClicked, app, Signals.tickerClicked)
        self.tickerTable.verticalHeader().hide()

    def on_splitter_splitterMoved(self, pos, index):
        """ Signal handler for splitter move; saves state to user settings.

        @param pos ignored
        @param index ignored
        @return None
        """
        settings = self.settings
        settings.beginGroup(self.__class__.__name__)
        settings.setValue(settings.keys.splitstate, self.splitter.saveState())
        settings.endGroup()

    def setSession(self, session):
        """ Configures this instance for a session.

        @param session Session instance
        @return None
        """
        self.session = session
        symbols = session.strategy.symbols()
        replayTickerMessages(session.messages, symbols,
                             self.on_session_TickPrice_TickSize)
        replayPortfolio(session.messages, self.on_session_UpdatePortfolio)
        session.registerMeta(self)
        if not session.messages:
            for tickerId in symbols.values():
                for msg in fakeTickerMessages(tickerId):
                    self.on_session_TickPrice_TickSize(msg)

    def basicActions(self, index):
        """ Creates action and separator list suitable for a context menu.

        @param index QModelIndex instance
        @return list of suitable QActions
        """
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

    @pyqtSignature('')
    def closePosition(self):
        """ Emits a signal for a position to be closed.

        """
        print '## close position order dialog'

    def urlActions(self, symbol):
        """

        """
        actions = []
        settings = self.settings
        settings.beginGroup(self.settings.keys.urls)
        urls = settings.value(settings.keys.tickerurls, defaults.tickerUrls())
        settings.endGroup()
        urls = [str(s) for s in defaults.tickerUrls()]
        for url in urls:
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
        """ Creates an action for closing a position.

        @param row ticker table row number
        @return close action connected to close method, or None
        """
        act = None
        index = self.tickerTable.model().index(row, 1)
        if index and index.isValid():
            try:
                pos = float(index.data().toString())
            except (ValueError, ):
                pos = 0
            if pos:
                act = QAction('Close %s shares...' % abs(pos), None)
                self.connect(act, Signals.triggered, self.closePosition)
        return act

    @pyqtSignature('')
    def on_actionChart_triggered(self):
        """ Emits a signal for a ticker chart.

        """
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
        """ Emits a signal for an order dialog.

        """
        print '## order for ', self.actionOrder.data().toString()

    def tickerTableColumns(self):
        t = self.tickerTable
        return [(c, t.horizontalHeaderItem(c))
                for c in range(t.columnCount())]

    def tickerTableColumnField(self, field):
        t = self.tickerTable
        for c in range(t.columnCount()):
            i = t.horizontalHeaderItem(c)
            if field == itemTickField(i):
                return c

    def on_fieldsList_itemChanged(self, item):
        """ Add/drop a column when a field is checked/unchecked.

        """
        headerItemColumnMap = self.headerItemColumnMap
        tickerTable = self.tickerTable
        userItems = self.tickFieldSelect.checkedItems()
        field = itemTickField(item)

        if item.checkState():
            col = tickerTable.columnCount()
            tickerTable.insertColumn(col)
            header = headerItemColumnMap[field] = ValueTableItem()
            header.setText(item.text())
            setItemTickField(header, field)
            tickerTable.setHorizontalHeaderItem(col, header)
            for r in range(tickerTable.rowCount()):
                tickerTable.setItem(r, col, TickerTableItem())
        else:
            headers = self.tickerTableColumns()
            col = [c for c, i in headers if itemTickField(i)==field][0]
            tickerTable.removeColumn(col)
            del(headerItemColumnMap[field])

        settings = self.settings
        settings.beginGroup(self.__class__.__name__)
        saveFields = [itemTickField(i) for i in userItems]
        settings.setValueDump('selectedFields', saveFields)
        settings.endGroup()

    def on_tickerTable_customContextMenuRequested(self, pos):
        """ Display a context menu over the ticker table.

        """
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
        """ Emits an item from the ticker table as a signal argument.

        """
        if not index.isValid():
            return
        row, col = index.row(), index.column()
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
        """ Updates the position and market value columns in the ticker table.

        """
        sym = message.contract.m_symbol
        symbols = self.session.strategy.symbols()
        try:
            tid = symbols[sym]
            items = self.tickerIds[tid]
        except (KeyError, ):
            pass
        else:
            items[1].setValue(message.position)
            items[2].setValue(message.marketValue)

    def on_session_TickPrice_TickSize(self, message):
        """ Updates size and price columns in the ticker table.
        Creates rows as needed.

        """
        table = self.tickerTable
        if not table.columnCount():
            return
        tickerId = message.tickerId
        value = (message.price if hasattr(message, 'price') else message.size)
        try:
            row = self.tickerIds[tickerId]
        except (KeyError, ):
            items = table.newItemsRow()
            #for item in items:
            #    item.setValueAlign()
            row = self.tickerIds[tickerId] = items[0].row()
        col = self.tickerTableColumnField(message.field)
        if col is None:
            return
        item = table.item(row, col)
        if not hasattr(item, 'setValue'):
            return
        if item:
            item.setValue(value)


class TickerTableItem(ValueTableItem):
    """ Automatically aligned value table items.

    """
    def __init__(self):
        ValueTableItem.__init__(self)
        self.setValueAlign()






            #table.resizeColumnsToContents()
            #table.resizeRowsToContents()

if 0:
    if 0:
        if 0:
            symbols = self.session.strategy.symbols()
            try:
                sym = dict([(b, a) for a, b in symbols.items()])[tickerId]
            except (KeyError, ):
                ## something wrong -- we don't have data for the
                ## ticker symbol.  this can happen if the connection
                ## sends tick messages and we don't have a strategy
                ## loaded with the symbol (tickerId) defined.  how can
                ## this be fixed?
                return




#            items[0].setSymbol(sym)
#            items[0].tickerId = tid
#            for item in items[1:]:
#                item.setValueAlign()
#            table.sortItems(0)
#            table.resizeColumnsToContents()
#            table.resizeRowsToContents()

