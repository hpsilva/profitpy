#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import Qt, pyqtSignature
from PyQt4.QtGui import QAction, QIcon, QPushButton, QTabWidget

from profit.lib import Signals, tickerIdRole
from profit.widgets.accountdisplay import AccountDisplay
from profit.widgets.connectiondisplay import ConnectionDisplay
from profit.widgets.executionsdisplay import ExecutionsDisplay
from profit.widgets.messagedisplay import MessageDisplay
from profit.widgets.orderdisplay import OrderDisplay
from profit.widgets.plotdisplay import PlotDisplay
from profit.widgets.portfoliodisplay import PortfolioDisplay
from profit.widgets.tickerdisplay import TickerDisplay


def tabWidgetMethod(cls):
    def method(self, title):
        widget = cls(self.session, self)
        index = self.addTab(widget, title)
        return index
    return method


class CloseTabButton(QPushButton):
    def __init__(self, parent=None):
        QPushButton.__init__(self, parent)
        self.setIcon(QIcon(':images/icons/tab_remove.png'))
        self.setFlat(True)
        triggerAction = QAction(self)
        triggerAction.setShortcut('Ctrl+W')
        self.addAction(triggerAction)
        self.connect(triggerAction, Signals.triggered, self.click)


class CentralTabs(QTabWidget):
    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        self.session = None
        self.closeTabButton = closeTabButton = CloseTabButton(self)
        self.setCornerWidget(closeTabButton, Qt.TopRightCorner)
        window = self.window()
        connect = self.connect
        connect(self, Signals.currentChanged, self.on_currentChanged)
        connect(window, Signals.sessionCreated, self.on_session_created)
        connect(window, Signals.modelDoubleClicked, self.on_itemClicked)
        connect(closeTabButton, Signals.clicked,
                self.on_closeTabButton_clicked)

    def canCloseCurrent(self):
        try:
            return self.currentWidget().canClose()
        except (AttributeError, ):
            return True

    def on_currentChanged(self, index=None):
        self.closeTabButton.setEnabled(self.canCloseCurrent())

    def on_statusTWS(self):
        self.on_currentChanged()

    @pyqtSignature('')
    def on_closeTabButton_clicked(self):
        index = self.currentIndex()
        if index == getattr(self, 'connectionTabIndex', None):
            delattr(self, 'connectionTabIndex')
        widget = self.widget(index)
        self.removeTab(index)
        widget.setAttribute(Qt.WA_DeleteOnClose)
        widget.close()
        self.on_currentChanged()

    def on_session_created(self, session):
        self.session = session
        connect = self.connect
        connect(session, Signals.connectedTWS, self.on_statusTWS)
        connect(session, Signals.disconnectedTWS, self.on_statusTWS)

    def on_itemClicked(self, index): # item, col):
        text = str(index.data().toString())
        icon = QIcon(index.data(Qt.DecorationRole))
        tickerId, tickerIdValid = index.data(tickerIdRole).toInt()
        if tickerIdValid:
            self.on_symbolClicked(
                item=None, symbol=text, tickerId=tickerId, icon=icon)
        else:
            try:
                call = getattr(self, 'on_%sClicked' % text.lower())
                tabIndex = call(text)
            except (AttributeError, TypeError, ), exc:
                print '## session item create exception:', exc
            else:
                self.setCurrentIndex(tabIndex)
                self.setTabIcon(tabIndex, icon)

    def on_connectionClicked(self, text):
        try:
            index = self.connectionTabIndex
        except (AttributeError, ):
            widget = ConnectionDisplay(self.session, self)
            index = self.connectionTabIndex = self.addTab(widget, text)
        return index

    on_accountClicked = tabWidgetMethod(AccountDisplay)
    on_executionsClicked = tabWidgetMethod(ExecutionsDisplay)
    on_messagesClicked = tabWidgetMethod(MessageDisplay)
    on_ordersClicked = tabWidgetMethod(OrderDisplay)
    on_portfolioClicked = tabWidgetMethod(PortfolioDisplay)

    def on_tickersClicked(self, text):
        widget = TickerDisplay(self.session, self)
        index = self.addTab(widget, text)
        self.connect(widget, Signals.tickerClicked, self.on_symbolClicked)
        return index

    def on_symbolClicked(self, item, index=None, symbol=None,
                         tickerId=None, icon=None, *args):
        if item is not None:
            symbol = str(item.text())
            tickerId = item.tickerId
            icon = item.icon()
        widget = PlotDisplay(self)
        widget.setSession(self.session, tickerId, *args)
        index = self.addTab(widget, symbol)
        self.setTabIcon(index, icon)
        self.setCurrentIndex(index)
