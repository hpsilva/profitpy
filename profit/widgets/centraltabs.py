#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import Qt, pyqtSignature
from PyQt4.QtGui import QAction, QIcon, QPushButton, QTabWidget

from profit.lib import importItem
from profit.lib.core import Signals, tickerIdRole
from profit.lib.gui import SessionHandler
from profit.widgets.ui_closetabbutton import Ui_CloseTabButton
from profit.widgets.ui_detachtabbutton import Ui_DetachTabButton


def tabWidgetMethod(name, reloaded=False):
    def method(self, title):
        cls = importItem('profit.widgets.' + name, reloaded=reloaded)
        widget = cls(self)
        index = self.addTab(widget, title)
        return index
    return method


class CloseTabButton(QPushButton, Ui_CloseTabButton):
    def __init__(self, parent):
        QPushButton.__init__(self, parent)
        self.setupUi(self)
        self.addAction(self.actionCloseTab)


class DetachTabButton(QPushButton, Ui_DetachTabButton):
    def __init__(self, parent):
        QPushButton.__init__(self, parent)
        self.setupUi(self)
        self.addAction(self.actionDetachTab)


class CentralTabs(QTabWidget, SessionHandler):
    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        self.session = None
        self.closeTab = closeTab = CloseTabButton(self)
        self.detachTab = detachTab = DetachTabButton(self)
        self.setCornerWidget(closeTab, Qt.TopRightCorner)
        self.setCornerWidget(detachTab, Qt.TopLeftCorner)
        self.requestSession()
        window = self.window()
        connect = self.connect
        connect(window, Signals.modelClicked, self.showItemTab)
        connect(window, Signals.modelDoubleClicked, self.newItemTab)
        connect(closeTab, Signals.clicked, self.closeItemTab)
        connect(detachTab, Signals.clicked, self.detachItemTab)

    @pyqtSignature('')
    def closeItemTab(self):
        index = self.currentIndex()
        widget = self.widget(index)
        if widget:
            self.removeTab(index)
            widget.setAttribute(Qt.WA_DeleteOnClose)
            widget.close()

    @pyqtSignature('')
    def detachItemTab(self):
        index = self.currentIndex()
        widget = self.widget(index)
        icon = self.tabIcon(index)
        text = str(self.tabText(index))
        widget.setParent(self.window())
        widget.setWindowFlags(Qt.Window)
        widget.setWindowIcon(icon)
        try:
            widget.setWindowTitle(str(widget.windowTitle()) % text)
        except (TypeError, ):
            pass
        action = QAction('Close', widget)
        action.setShortcut('Ctrl+W')
        widget.addAction(action)
        widget.connect(action, Signals.triggered, widget.close)
        widget.show()

    def newItemTab(self, index):
        text = name = str(index.data().toString())
        text = text.replace(' ', '_').lower()
        icon = QIcon(index.data(Qt.DecorationRole))
        tickerId, tickerIdValid = index.data(tickerIdRole).toInt()
        if tickerIdValid:
            self.newSymbolItemTab(
                item=None, symbol=name, tickerId=tickerId, icon=icon)
        else:
            try:
                call = getattr(self, 'new_%sItem' % text)
                tabIndex = call(name)
            except (AttributeError, TypeError, ), exc:
                print '## session item create exception:', exc
            else:
                self.setCurrentIndex(tabIndex)
                self.setTabIcon(tabIndex, icon)

    def newSymbolItemTab(self, item, index=None, symbol=None,
                         tickerId=None, icon=None, *args):
        if item is not None:
            symbol = str(item.text())
            tickerId = item.tickerId
            icon = item.icon()
        cls = importItem('profit.widgets.tickerplotdisplay.TickerPlotDisplay')
        widget = cls(self)
        widget.setSessionPlot(
            self.session, self.session.tickerCollection, tickerId, *args)
        index = self.addTab(widget, symbol)
        self.setTabIcon(index, icon)
        self.setCurrentIndex(index)

    def showItemTab(self, index):
        name = index.data().toString()
        pages = dict([(self.tabText(i), i) for i in range(self.count())])
        if name in pages:
            self.setCurrentIndex(pages[name])
        else:
            self.newItemTab(index)

    # handlers for the various named items in the session widget

    new_accountItem = tabWidgetMethod('accountdisplay.AccountDisplay')
    new_connectionItem = tabWidgetMethod(
        'connectiondisplay.ConnectionDisplay')
    new_executionsItem = tabWidgetMethod(
        'executionsdisplay.ExecutionsDisplay')
    new_messagesItem = tabWidgetMethod('messagedisplay.MessageDisplay')
    new_ordersItem = tabWidgetMethod('orderdisplay.OrderDisplay')
    new_portfolioItem = tabWidgetMethod('portfoliodisplay.PortfolioDisplay')
    new_strategyItem = tabWidgetMethod('strategydisplay.StrategyDisplay')

    new_tickersItemHelper = tabWidgetMethod('tickerdisplay.TickerDisplay')
    def new_tickersItem(self, text):
        index = self.new_tickersItemHelper(text)
        widg = self.widget(index)
        self.connect(widg, Signals.tickerClicked, self.newSymbolItemTab)
        return index

