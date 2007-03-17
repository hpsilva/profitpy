#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import Qt, pyqtSignature
from PyQt4.QtGui import QAction, QIcon, QPushButton, QTabWidget

from profit.lib import importItem
from profit.lib.core import Signals, tickerIdRole
from profit.widgets.ui_closetabbutton import Ui_CloseTabButton
from profit.widgets.ui_detachtabbutton import Ui_DetachTabButton


def tabWidgetMethod(name):
    def method(self, title):
        cls = importItem('profit.widgets.' + name)
        widget = cls(self.session, self)
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


class CentralTabs(QTabWidget):
    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        self.session = None
        self.connectionTabIndex = None
        self.closeTab = closeTab = CloseTabButton(self)
        self.detachTab = detachTab = DetachTabButton(self)
        self.setCornerWidget(closeTab, Qt.TopRightCorner)
        self.setCornerWidget(detachTab, Qt.TopLeftCorner)
        window = self.window()
        connect = self.connect
        connect(self, Signals.currentChanged, self.on_currentChanged)
        connect(window, Signals.sessionCreated, self.on_session_created)
        connect(window, Signals.modelDoubleClicked, self.on_itemClicked)
        connect(closeTab, Signals.clicked, self.on_closeTab_clicked)
        connect(detachTab, Signals.clicked, self.on_detachTab_clicked)

    def canCloseCurrent(self):
        try:
            return self.currentWidget().canClose()
        except (AttributeError, ):
            return True

    on_accountClicked = tabWidgetMethod('accountdisplay.AccountDisplay')
    on_account_supervisorClicked = \
        tabWidgetMethod('accountsupervisor.AccountSupervisorDisplay')

    @pyqtSignature('')
    def on_closeTab_clicked(self):
        index = self.currentIndex()
        if index == self.connectionTabIndex:
            self.connectionTabIndex = None
        widget = self.widget(index)
        self.removeTab(index)
        widget.setAttribute(Qt.WA_DeleteOnClose)
        widget.close()
        self.on_currentChanged()

    def on_connectionClicked(self, text):
        index = self.connectionTabIndex
        if index is None:
            cls = importItem(
                'profit.widgets.connectiondisplay.ConnectionDisplay')
            widget = cls(self.session, self)
            index = self.connectionTabIndex = self.addTab(widget, text)
        return index

    @pyqtSignature('int')
    def on_currentChanged(self, index=None):
        self.closeTab.setEnabled(self.canCloseCurrent())
        self.detachTab.setEnabled(
            self.connectionTabIndex != self.currentIndex())

    @pyqtSignature('')
    def on_detachTab_clicked(self):
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
        self.on_currentChanged()

    on_executionsClicked = \
        tabWidgetMethod('executionsdisplay.ExecutionsDisplay')

    def on_itemClicked(self, index):
        text = name = str(index.data().toString())
        text = text.replace(' ', '_').lower()
        icon = QIcon(index.data(Qt.DecorationRole))
        tickerId, tickerIdValid = index.data(tickerIdRole).toInt()
        if tickerIdValid:
            self.on_symbolClicked(
                item=None, symbol=name, tickerId=tickerId, icon=icon)
        else:
            try:
                call = getattr(self, 'on_%sClicked' % text)
                tabIndex = call(name)
            except (AttributeError, TypeError, ), exc:
                print '## session item create exception:', exc
            else:
                self.setCurrentIndex(tabIndex)
                self.setTabIcon(tabIndex, icon)
        if self.count() == 1:
            self.on_currentChanged()

    on_messagesClicked = tabWidgetMethod('messagedisplay.MessageDisplay')
    on_ordersClicked = tabWidgetMethod('orderdisplay.OrderDisplay')
    on_order_supervisorClicked = \
        tabWidgetMethod('ordersupervisor.OrderSupervisorDisplay')
    on_portfolioClicked = \
        tabWidgetMethod('portfoliodisplay.PortfolioDisplay')

    def on_session_created(self, session):
        self.session = session
        connect = self.connect
        connect(session, Signals.connectedTWS, self.on_statusTWS)
        connect(session, Signals.disconnectedTWS, self.on_statusTWS)

    def on_statusTWS(self):
        self.on_currentChanged()

    on_strategyClicked = \
        tabWidgetMethod('strategydisplay.StrategyDisplay')

    def on_symbolClicked(self, item, index=None, symbol=None,
                         tickerId=None, icon=None, *args):
        if item is not None:
            symbol = str(item.text())
            tickerId = item.tickerId
            icon = item.icon()
        cls = importItem('profit.widgets.plotdisplay.PlotDisplay')
        widget = cls(self)
        widget.setSession(self.session, tickerId, *args)
        index = self.addTab(widget, symbol)
        self.setTabIcon(index, icon)
        self.setCurrentIndex(index)

    def on_tickersClicked(self, text):
        cls = importItem('profit.widgets.tickerdisplay.TickerDisplay')
        widget = cls(self.session, self)
        index = self.addTab(widget, text)
        self.connect(widget, Signals.tickerClicked, self.on_symbolClicked)
        return index

    on_trade_indicatorClicked = \
        tabWidgetMethod('tradeindicator.TradeIndicatorDisplay')
