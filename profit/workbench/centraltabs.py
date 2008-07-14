#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from functools import partial
from sys import platform

from PyQt4.QtCore import QTimer, Qt, pyqtSignature
from PyQt4.QtGui import QAction, QApplication, QIcon, QTabWidget

from profit.lib import importItem, logging
from profit.lib.core import SessionHandler, Signals, DataRoles
from profit.lib.widgets.buttons import CloseTabButton, DetachTabButton
from profit.workbench.tickerplotdisplay import TickerPlotDisplay
from profit.lib.widgets.webbrowser import WebBrowserDisplay


displayClasses = {
    'account' : 'accountdisplay.AccountDisplay',
    'collector' : 'collectordisplay.CollectorDisplay',
    'connection' : 'connectiondisplay.ConnectionDisplay',
    'execution' : 'executionsdisplay.ExecutionsDisplay',
    'historical data' : 'historicaldatadisplay.HistoricalDataDisplay',
    'messages' : 'messagedisplay.MessageDisplay',
    'orders' : 'orderdisplay.OrderDisplay',
    'portfolio' : 'portfoliodisplay.PortfolioDisplay',
    'strategy' : 'strategydisplay.StrategyDisplay',
    'tickers' : 'tickerdisplay.TickerDisplay',
}


class CentralTabs(QTabWidget, SessionHandler):
    """ CentralTabs -> tab widget with special powers

    """
    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        self.closeTabButton = CloseTabButton(self)
        self.detachTabButton = DetachTabButton(self)
        self.setCornerWidget(self.closeTabButton, Qt.TopRightCorner)
        self.setCornerWidget(self.detachTabButton, Qt.TopLeftCorner)
        app, connect = QApplication.instance(), self.connect
        connect(app, Signals.sessionItemActivated, self.createTab)
        connect(app, Signals.openUrl, self.createTab)
        connect(app, Signals.tickerClicked, self.createTab)
        connect(self.closeTabButton, Signals.clicked, self.closeTab)
        connect(self.detachTabButton, Signals.clicked, self.detachTab)
        self.requestSession()

    def createTab(self, value):
        """ create or display a tab from a value; value may be a string or a model item

        """
        handlers = [self.createBrowserTab, 
                    self.createTickerPlotTab,
                    self.createDisplayTab]
        for handler in handlers:
            try:
                if handler(value):
                    break
            except (Exception, ), exc:
                pass

    def createBrowserTab(self, item):
        """ creates a new web browser tab.

        """
        if hasattr(item, 'toolTip'):
            url, title = item.data().toString(), item.toolTip()
        else:
            #url, title = item.data().toString(), ''
            return False
        widget = WebBrowserDisplay(self)
        widget.basicConfig(url)
        index = self.addTab(widget, title)
        self.setTextIconCurrentTab(index, title, QIcon(":/images/icons/www.png"))
        self.connect(widget, Signals.loadFinished, 
                     partial(self.resetBrowserTab, browser=widget))
        return True

    def createTickerPlotTab(self, item):
        """ creates or displays a ticker plot tab

        """
        tickerId, tickerIdValid = item.data(DataRoles.tickerId).toInt()
        symbol = str(item.data(DataRoles.tickerSymbol).toString())
        if tickerIdValid and self.setCurrentLabel(symbol):
            return
        if tickerIdValid:
            widget = TickerPlotDisplay(self)
            session = self.session
            widget.setSessionPlot(session, session.tickerCollection, tickerId)
            index = self.addTab(widget, symbol)
            icon = QIcon(item.data(Qt.DecorationRole))
            self.setTextIconCurrentTab(index, symbol, icon)
            return True

    def createDisplayTab(self, item):
        """ creates or displays a name-based display

        """
        text = str(item.data().toString())
        if self.setCurrentLabel(text):
            return
        name = displayClasses.get(text.lower(), None)
        if name is not None:
            cls = importItem('profit.workbench.%s' % name)
            widget = cls(self)
            index = self.addTab(widget, text)
            self.setTextIconCurrentTab(index, text, QIcon(item.data(Qt.DecorationRole)))
            return True

    def pageMap(self):
        """ makes a mapping like {'connection':1, 'account':3, ...}

        """
        return dict([(str(self.tabText(i)), i) for i in range(self.count())])

    def closeTab(self):
        """ slot that closes the current tab tab

        """
        index = self.currentIndex()
        widget = self.widget(index)
        if widget:
            self.removeTab(index)
            widget.setAttribute(Qt.WA_DeleteOnClose)
            widget.close()

    def detachTab(self):
        """ slot that deatches the current tab and makes it a top-level window

        """
        index = self.currentIndex()
        widget, icon = self.widget(index), self.tabIcon(index)
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
        QTimer.singleShot(100, show)

    def resetBrowserTab(self, okay, browser=None):
        """ slot to reconfigure a tab based on a web browser widget state

        """
        if not okay or not browser:
            return
        index = self.indexOf(browser)
        title = tooltip = str(browser.title())
        if len(title) > 13:
            title = title[0:13] + '...'
        self.setTabText(index, title)
        self.setTabToolTip(index, tooltip)

    def setTextIconCurrentTab(self, index, text, icon):
        """ sets a tabs text and icon, and makes tab current

        """
        self.setTabText(index, text)
        self.setTabIcon(index, icon)
        self.setCurrentIndex(index)

    def setCurrentLabel(self, label):
        """ sets current tab by name if available; returns true if successful

        """
        index = self.pageMap().get(label, None)
        if index is not None:
            self.setCurrentIndex(index)
            return True
