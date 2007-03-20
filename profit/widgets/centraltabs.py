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


def tabWidgetMethod(name, reloaded=False):
    def method(self, title):
        cls = importItem('profit.widgets.' + name, reloaded=reloaded)
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
        self.closeTab = closeTab = CloseTabButton(self)
        self.detachTab = detachTab = DetachTabButton(self)
        self.setCornerWidget(closeTab, Qt.TopRightCorner)
        self.setCornerWidget(detachTab, Qt.TopLeftCorner)
        window = self.window()
        connect = self.connect
        connect(window, Signals.sessionCreated, self.on_session_created)
        connect(window, Signals.modelDoubleClicked, self.on_item_clicked)
        connect(closeTab, Signals.clicked, self.on_closeTab_clicked)
        connect(detachTab, Signals.clicked, self.on_detachTab_clicked)

    @pyqtSignature('')
    def on_closeTab_clicked(self):
        index = self.currentIndex()
        widget = self.widget(index)
        if widget:
            self.removeTab(index)
            widget.setAttribute(Qt.WA_DeleteOnClose)
            widget.close()

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

    def on_item_clicked(self, index):
        text = name = str(index.data().toString())
        text = text.replace(' ', '_').lower()
        icon = QIcon(index.data(Qt.DecorationRole))
        tickerId, tickerIdValid = index.data(tickerIdRole).toInt()
        if tickerIdValid:
            self.on_symbol_clicked(
                item=None, symbol=name, tickerId=tickerId, icon=icon)
        else:
            try:
                call = getattr(self, 'on_%s_clicked' % text)
                tabIndex = call(name)
            except (AttributeError, TypeError, ), exc:
                print '## session item create exception:', exc
            else:
                self.setCurrentIndex(tabIndex)
                self.setTabIcon(tabIndex, icon)

    def on_session_created(self, session):
        self.session = session

    def on_symbol_clicked(self, item, index=None, symbol=None,
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

    def on_tickers_clicked(self, text):
        cls = importItem('profit.widgets.tickerdisplay.TickerDisplay')
        widget = cls(self.session, self)
        index = self.addTab(widget, text)
        self.connect(widget, Signals.tickerClicked, self.on_symbol_clicked)
        return index

    on_account_clicked = \
        tabWidgetMethod('accountdisplay.AccountDisplay', reloaded=True)
    on_account_supervisor_clicked = \
        tabWidgetMethod('accountsupervisor.AccountSupervisorDisplay')
    on_connection_clicked = \
        tabWidgetMethod('connectiondisplay.ConnectionDisplay')
    on_executions_clicked = \
        tabWidgetMethod('executionsdisplay.ExecutionsDisplay')
    on_messages_clicked = \
        tabWidgetMethod('messagedisplay.MessageDisplay')
    on_orders_clicked = \
        tabWidgetMethod('orderdisplay.OrderDisplay')
    on_order_supervisor_clicked = \
        tabWidgetMethod('ordersupervisor.OrderSupervisorDisplay')
    on_portfolio_clicked = \
        tabWidgetMethod('portfoliodisplay.PortfolioDisplay')
    on_strategy_clicked = \
        tabWidgetMethod('strategydisplay.StrategyDisplay')
    on_trade_indicator_clicked = \
        tabWidgetMethod('tradeindicator.TradeIndicatorDisplay')
