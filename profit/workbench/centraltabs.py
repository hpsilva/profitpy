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


def basicTabMethod(name, prefix='profit.workbench', pre=None, post=None, reloaded=False):
    """ creates and returns an object method for handling new tab requests

    The closures created by this function are used in the CentralTabs
    class below.
    """
    def innerMethod(self, title, itemIndex=None):
        logging.debug('%s %s', name, title)
        index = None
        if pre:pre(self)
        if itemIndex:
            pages = self.pageMap()
            index = pages.get(itemIndex.data().toString(), None)
        if index is None:
            cls = importItem('%s.%s' % (prefix, name), reloaded=reloaded)
            widget = cls(self)
            index = self.addTab(widget, title)
            if post:post(self, widget)
        return index
    return innerMethod


class CentralTabs(QTabWidget, SessionHandler):
    """ CentralTabs -> tab widget with special powers

    """
    def create_url_tab(self, item):
        try:
            url = str(item.toString())
            self.newBrowserTab(url)
            return url
        except (AttributeError, ):
            return False

    def create_ticker_plot_tab(self, item):
        try:
            tickerId, tickerIdValid = item.data(DataRoles.tickerId).toInt()
            if tickerIdValid:
                name = str(item.data().toString())
                icon = QIcon(item.data(Qt.DecorationRole))
                self.newSymbolTab(None, symbol=name, tickerId=tickerId, icon=icon)
                return True
        except (AttributeError, ):
            return False

    def create_ticker_tab(self, item):
        try:
            if str(item.data().toString()) == 'tickers':

                def post(self, widget):
                    self.connect(widget, Signals.tickerClicked,
                                 self.newSymbolTab)
                newTickersTab = basicTabMethod('tickerdisplay.TickerDisplay',
                                               post=post)
                newTickersTab(self, 'tickers')
                return True
        except (Exception, ), exc:
            logging.exception('## Exception %s', exc)
        return False

    def create_basic_tab(self, item):
        text = str(item.data().toString())
        if text.lower() in self.moduleClassMap:
            method = basicTabMethod(self.moduleClassMap[text])
            tabIndex = method(self, text)
            icon = QIcon(item.data(Qt.DecorationRole))
            self.setCurrentIndex(tabIndex)
            self.setTabIcon(tabIndex, icon)
            return True

    moduleClassMap = {
        'account' : 'accountdisplay.AccountDisplay',
        'collector' : 'collectordisplay.CollectorDisplay',
        'connection' : 'connectiondisplay.ConnectionDisplay',
        'execution' : 'executionsdisplay.ExecutionsDisplay',
        'historical data' : 'historicaldatadisplay.HistoricalDataDisplay',
        'messages' : 'messagedisplay.MessageDisplay',
        'orders' : 'orderdisplay.OrderDisplay',
        'portfolio' : 'portfoliodisplay.PortfolioDisplay',
        'strategy' : 'strategydisplay.StrategyDisplay',
    }

    createHandlers = [
        create_url_tab,
        create_ticker_tab,
        create_ticker_plot_tab,
        create_basic_tab,
        ]

    def handleItem(self, item):
        actual = None
        for handler in self.createHandlers:
            if handler(self, item):
                actual = handler
                break
        logging.debug('actual handler: %s', actual)


    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        self.closeTabButton = CloseTabButton(self)
        self.detachTabButton = DetachTabButton(self)
        self.setCornerWidget(self.closeTabButton, Qt.TopRightCorner)
        self.setCornerWidget(self.detachTabButton, Qt.TopLeftCorner)
        app, connect = QApplication.instance(), self.connect
        connect(app, Signals.sessionItemActivated, self.handleItem)
        connect(app, Signals.openUrl, self.handleItem)
        connect(self.closeTabButton, Signals.clicked, self.closeTab)
        connect(self.detachTabButton, Signals.clicked, self.detachTab)
        self.requestSession()

    def pageMap(self):
        """ makes a mapping of tabtitle:tabindex

        """
        return dict([(self.tabText(i), i) for i in range(self.count())])

    def newBrowserTab(self, itemData):
        """ slot for creating a new web browser tab

        """
        from profit.lib.widgets.webbrowser import WebBrowserDisplay
        if hasattr(itemData, 'toolTip'):
            url, title = itemData.data().toString(), itemData.toolTip()
        else:
            url, title = itemData, ''
        widget = WebBrowserDisplay(self)
        widget.basicConfig(url)
        index = self.addTab(widget, title)
        self.setCurrentIndex(index)
        self.setTabText(index, title)
        self.setTabIcon(index, QIcon(":/images/icons/www.png"))
        self.connect(widget, Signals.loadFinished,
                     partial(self.resetBrowserTab, browser=widget))

    def newSymbolTab(self, item, index=None, symbol=None, tickerId=None, icon=None, *args):
        """ slot for creating a new symbol display tab

        """
        from profit.workbench.tickerplotdisplay import TickerPlotDisplay
        if item is not None:
            symbol = str(item.text())
            tickerId = item.tickerId
            icon = item.icon()
        widget = TickerPlotDisplay(self)
        session = self.session
        widget.setSessionPlot(session, session.tickerCollection, tickerId, *args)
        index = self.addTab(widget, symbol)
        self.setTabIcon(index, icon)
        self.setCurrentIndex(index)

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

    @pyqtSignature('')
    def closeTab(self):
        """ slot that closes the current tab tab

        """
        index = self.currentIndex()
        widget = self.widget(index)
        if widget:
            self.removeTab(index)
            widget.setAttribute(Qt.WA_DeleteOnClose)
            widget.close()

    @pyqtSignature('')
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
        show.circleref = show
        QTimer.singleShot(100, show)
