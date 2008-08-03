#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from functools import partial
from itertools import ifilter
from string import Template

from PyQt4.QtCore import QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QAction, QFrame, QIcon, QMenu

from ib.opt.message import TickPrice

from profit.lib import (
    BasicHandler, DataRoles, Signals, defaults, instance, makeCheckNames, )
from profit.lib.gui import (
    UrlRequestor, ValueTableItem, separator, makeUrlAction, symbolIcon, )
from profit.lib.widgets.tickfieldselect import (
    ExField, fieldIds, itemTickField, setItemTickField, )

#from profit.workbench.portfoliodisplay import replayPortfolio
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
                callback(message, replay=True)
                break


def fakeTickerMessages(tickerId):
    """ Generates fake TickPrice messages for every ticker field

    @param tickerId ticker id
    @return None
    """
    tick = partial(TickPrice, tickerId=tickerId, price=0, canAutoExecute=False)
    for field in fieldIds():
        yield tick(field=field)


valueCache = {}


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
        self.tickerIds = {}
        self.extraFieldItemSetups = {
            ExField.tid : self.setIdItem,
            ExField.sym : self.setSymbolItem,
            ExField.pos : self.setPositionItem,
            ExField.val : self.setPositionValueItem,
        }
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
        defaultState = defaults.rightSplitterState()
        splitState = settings.value(settings.keys.splitstate, defaultState)
        self.splitter.restoreState(splitState.toByteArray())
        settings.endGroup()
        app = instance()
        connect = self.connect
        connect(self, Signals.openUrl, app, Signals.openUrl)
        connect(self, Signals.tickerClicked, app, Signals.tickerClicked)
        self.tickerTable.verticalHeader().hide()

    def setSession(self, session):
        """ Configures this instance for a session.

        @param session Session instance
        @return None
        """
        self.session = session
        model = session.models.tickers
        model.symbolIcon = symbolIcon
        #self.connect(model, Signals.modelReset, self.resizeTree)
        self.tickersView.setModel(model)

        symbols = session.strategy.symbols()
        #replayTickerMessages(session.messages, symbols,
        #                     self.on_session_TickPrice_TickSize)
        #replayPortfolio(session.messages, self.on_session_UpdatePortfolio)
        session.registerMeta(self)
#        if not session.messages:
#            for tickerId in symbols.values():
#                for msg in fakeTickerMessages(tickerId):
#                    self.on_session_TickPrice_TickSize(msg)

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

    def fieldColumn(self, field, default=None):
        """ Returns the ticker table column number for the given field.

        This method could move to a TickerTable(QTableWidget) class.

        @param field TickType field
        @param default=None value returned if column not found
        """
        table = self.tickerTable
        for col in range(table.columnCount()):
            if field == itemTickField(table.horizontalHeaderItem(col)):
                return col
        return default

    def makeTickerColumn(self, field, label):
        """ Constructs a new column and a header for the ticker table.

        @param field TickType field
        @param label header label
        @return new column number
        """
        table = self.tickerTable
        column = table.columnCount()
        table.insertColumn(column)
        header = ValueTableItem()
        header.setText(label)
        setItemTickField(header, field)
        table.setHorizontalHeaderItem(column, header)
        return column

    def makeTickerColumnItems(self, column):
        """ Creates ticker table items for (new) column.

        @param column table column
        @return None
        """
        table = self.tickerTable
        for row in range(table.rowCount()):
            item = ValueTableItem()
            item.setValueAlign()
            table.setItem(row, column, item)

    def setupFieldColumn(self, field, column):
        """ Configures column items as much as possible.

        This method maps existing ticker fields to items at the given
        column.  We don't mix this behavior with the column
        construction (makeTickerColumnItems) because that would muddle the
        behavior.

        @param field TickType field
        @param column table column
        @return None
        """
        extraFieldItemSetups = self.extraFieldItemSetups
        tickerTable = self.tickerTable
        for tickerId, row in self.tickerIds.items():
            item = tickerTable.item(row, column)
            if item:
                if field in extraFieldItemSetups:
                    extraFieldItemSetups[field](item, tickerId)
                else:
                    value = valueCache.get(tickerId, {}).get(field, '')
                    item.setValue(value)

    def makeTickerRow(self, tickerId):
        """ Creates a ticker table row for the given tickerId.

        @param tickerId yes, that
        @return id of new row

        """
        table = self.tickerTable
        items = table.newItemsRow()
        extraFieldItemSetups = self.extraFieldItemSetups
        for col, item in enumerate(items):
            item.setValueAlign()
            field = itemTickField(table.horizontalHeaderItem(col))
            if field in extraFieldItemSetups:
                extraFieldItemSetups[field](item, tickerId)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        return table.rowCount()

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

    def on_fieldsList_itemChanged(self, item):
        """ Add/drop a column when a field is checked/unchecked.

        """
        table = self.tickerTable
        field = itemTickField(item)
        if item.checkState():
            col = self.makeTickerColumn(field, item.text())
            self.makeTickerColumnItems(col)
            self.setupFieldColumn(field, col)
            table.resizeColumnToContents(col)
        else:
            table.removeColumn(self.fieldColumn(field))
        self.saveFieldSelections()

    def on_session_UpdatePortfolio(self, message):
        """ Updates the position and market value columns in the ticker table.

        """

        ## TODO: fix references, i.e., make contract lookup precise,
        ## and also locate column by contract (or
        ## by message.contract symbol+secType+expiry+etc)

        sym = message.contract.m_symbol
        symbols = self.session.strategy.symbols()
        try:
            tid = symbols[sym]
            row = self.tickerIds[tid]
        except (KeyError, ):
            return
        items = ((ExField.val, message.marketValue),
                 (ExField.pos, message.position),
                 )
        table = self.tickerTable
        for field, value in items:
            col = self.fieldColumn(field)
            if col is not None:
                item = table.item(row, col)
                if item:
                    item.setValue(value)

    def on_session_TickPrice_TickSize(self, message):
        """ Updates size and price columns in the ticker table.
        Creates rows as needed.

        """
        field = message.field
        value = (message.price if hasattr(message, 'price') else message.size)
        tickerTable = self.tickerTable
        tickerId = message.tickerId
        valueCache.setdefault(tickerId, {})[field] = value
        col = self.fieldColumn(field)
        if col is None:
            return
        try:
            row = self.tickerIds[tickerId]
        except (KeyError, ):
            row = self.tickerIds[tickerId] = self.makeTickerRow(tickerId)
        item = tickerTable.item(row, col)
        if item:
            item.setValue(value)

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

    def saveFieldSelections(self):
        """ Saves the selected fields.

        """
        settings = self.settings
        settings.beginGroup(self.__class__.__name__)
        userItems = self.tickFieldSelect.checkedItems()
        saveFields = [itemTickField(i) for i in userItems]
        settings.setValueDump('selectedFields', saveFields)
        settings.endGroup()

    def urlActions(self, symbol):
        """ Returns a list of actions for the given symbol.

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
            request = partial(self.requestUrl, action=act)
            self.connect(act, Signals.triggered, request)
            actions.append(act)
        return actions

    ## table item setter-uppers

    def setIdItem(self, item, tickerId):
        """ Configures an item for the 'Id' column.

        """
        item.setText(tickerId)
        item.setValueAlign(Qt.AlignLeft|Qt.AlignVCenter)

    def setSymbolItem(self, item, tickerId):
        """ Configures an item for the 'Symbol' column.

        """
        symbols = self.session.strategy.symbols()
        try:
            sym = dict([(b, a) for a, b in symbols.items()])[tickerId]
        except (KeyError, ):
            pass
        else:
            item.setSymbol(sym)
            item.setValueAlign(Qt.AlignLeft|Qt.AlignVCenter)

    def setPositionItem(self, item, tickerId):
        """ Configures an item for the 'Position' column.

        """

    def setPositionValueItem(self, item, tickerId):
        """ Configures an item for the 'Value' column.

        """
