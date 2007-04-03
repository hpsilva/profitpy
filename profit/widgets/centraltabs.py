#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from sys import platform

from PyQt4.QtCore import QTimer, Qt, pyqtSignature
from PyQt4.QtGui import QAction, QApplication, QIcon, QPushButton, QTabWidget

from profit.lib import importItem, logging
from profit.lib.core import SessionHandler, Signals, tickerIdRole
from profit.widgets.ui_closetabbutton import Ui_CloseTabButton
from profit.widgets.ui_detachtabbutton import Ui_DetachTabButton


disallowMultiples = ['strategydisplay.StrategyDisplay', ]


def tabWidgetMethod(name, reloaded=False):
    def method(self, title, itemindex=None):
        cls = importItem('profit.widgets.' + name, reloaded=reloaded)
        index = None
        if name in disallowMultiples and itemindex:
            pages = self.pageMap()
            index = pages.get(itemindex.data().toString(), None)
        if index is None:
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
        self.closeTab = closeTab = CloseTabButton(self)
        self.detachTab = detachTab = DetachTabButton(self)
        self.setCornerWidget(closeTab, Qt.TopRightCorner)
        self.setCornerWidget(detachTab, Qt.TopLeftCorner)
        self.requestSession()
        app = QApplication.instance()
        connect = self.connect
        connect(app, Signals.sessionItemSelected, self.showItemTab)
        connect(app, Signals.sessionItemActivated, self.newItemTab)
        connect(closeTab, Signals.clicked, self.closeItemTab)
        connect(detachTab, Signals.clicked, self.detachItemTab)

    def pageMap(self):
        return dict([(self.tabText(i), i) for i in range(self.count())])

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
        widget.setWindowIcon(icon)
        try:
            widget.setWindowTitle(str(widget.windowTitle()) % text)
        except (TypeError, ):
            pass
        action = QAction('Close', widget)
        action.setShortcut('Ctrl+W')
        widget.addAction(action)
        widget.connect(action, Signals.triggered, widget.close)
        if platform.startswith('win'):
            def show():
                widget.setParent(QApplication.desktop())
                widget.setWindowFlags(Qt.Dialog)
                widget.show()
        else:
            def show():
                widget.setParent(self.window())
                widget.setWindowFlags(Qt.Window)
                widget.show()
        show.circleref = show
        QTimer.singleShot(100, show)

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
                tabIndex = call(name, index)
            except (Exception, ), exc:
                logging.debug('Session item create exception: %s', exc)
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
        pages = self.pageMap()
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
    def new_tickersItem(self, text, itemindex):
        index = self.new_tickersItemHelper(text, itemindex)
        widg = self.widget(index)
        self.connect(widg, Signals.tickerClicked, self.newSymbolItemTab)
        return index

