#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from functools import partial
from sys import platform

from PyQt4.QtCore import QTimer, QUrl, Qt, pyqtSignature
from PyQt4.QtGui import QAction, QApplication, QIcon, QPushButton, QTabWidget

from profit.lib import importItem, logging
from profit.lib.core import SessionHandler, Signals, tickerIdRole
from profit.lib.widgets.ui_closetabbutton import Ui_CloseTabButton
from profit.lib.widgets.ui_detachtabbutton import Ui_DetachTabButton


def basicTabMethod(name, prefix='profit.workbench', pre=None, post=None,
              reloaded=False):
    def innerMethod(self, title, itemIndex=None):
        logging.debug('%s %s', name, title)
        index = None
        if pre:pre(self)
        if itemIndex:
            index = self.pageMap().get(itemIndex.data().toString(), None)
        if index is None:
            cls = importItem('%s.%s' % (prefix, name), reloaded=reloaded)
            widget = cls(self)
            index = self.addTab(widget, title)
            if post:post(self, widget)
        return index
    return innerMethod


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
        self.closeTabButton = CloseTabButton(self)
        self.detachTabButton = DetachTabButton(self)
        self.setCornerWidget(self.closeTabButton, Qt.TopRightCorner)
        self.setCornerWidget(self.detachTabButton, Qt.TopLeftCorner)
        app, connect = QApplication.instance(), self.connect
        connect(app, Signals.sessionItemSelected, self.showTab)
        connect(app, Signals.sessionItemActivated, self.newTab)
        connect(self.closeTabButton, Signals.clicked, self.closeTab)
        connect(self.detachTabButton, Signals.clicked, self.detachTab)
        self.requestSession()

    def pageMap(self):
        """ makes a mapping of tabtitle:tabindex

        """
        return dict([(self.tabText(i), i) for i in range(self.count())])

    def showTab(self, index):
        """ shows an existing tab or creates a new one

        """
        name = index.data().toString()
        pages = self.pageMap()
        if name in pages:
            self.setCurrentIndex(pages[name])
        else:
            self.newTab(index)

    def newTab(self, index):
        """ create a new tab

        """
        text = name = str(index.data().toString())
        text = text.replace(' ', '_').lower()
        icon = QIcon(index.data(Qt.DecorationRole))
        tickerId, tickerIdValid = index.data(tickerIdRole).toInt()
        ## why do we have to switch on the type of session tree item?
        ## can't we direct let the session item determine what method
        ## we call and how??
        if tickerIdValid:
            self.newSymbolTab(None, symbol=name, tickerId=tickerId, icon=icon)
        else:
            try:
                call = getattr(self, 'new%sTab' % text.title())
                tabIndex = call(name, index)
                self.setCurrentIndex(tabIndex)
                self.setTabIcon(tabIndex, icon)
            except (Exception, ), exc:
                message = 'Session item create exception: "%s" name: "%s"'
                logging.debug(message, exc, name)

    def newBrowserTab(self, itemData):
        from profit.lib.widgets.webbrowser import WebBrowserDisplay
        try:
            url, title, icon = itemData.toPyObject()
        except (AttributeError, ):
            url, title, icon = itemData
        widget = WebBrowserDisplay(self)
        index = self.addTab(widget, title)
        widget.basicConfig(url)
        self.setCurrentIndex(index)
        self.connect(widget, Signals.loadFinished,
                     partial(self.setWebTab, browser=widget))
        self.setTabText(index, title)
        self.setTabIcon(index, icon)

    def newSymbolTab(self, item, index=None, symbol=None, tickerId=None,
                     icon=None, *args):
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

    newAccountTab = basicTabMethod('accountdisplay.AccountDisplay')
    newCollectorTab = basicTabMethod('collectordisplay.CollectorDisplay')
    newConnectionTab = basicTabMethod('connectiondisplay.ConnectionDisplay')
    newExecutionsTab = basicTabMethod('executionsdisplay.ExecutionsDisplay')
    newMessagesTab = basicTabMethod('messagedisplay.MessageDisplay')
    newOrdersTab = basicTabMethod('orderdisplay.OrderDisplay')
    newPortfolioTab = basicTabMethod('portfoliodisplay.PortfolioDisplay')
    newStrategyTab = basicTabMethod('strategydisplay.StrategyDisplay')

    def afterNewTickers(self, widget):
        self.connect(widget, Signals.openUrl, self.newBrowserTab)
        self.connect(widget, Signals.tickerClicked, self.newSymbolTab)
    newTickersTab = basicTabMethod('tickerdisplay.TickerDisplay',
                                   post=afterNewTickers)

    def setWebTab(self, okay, browser):
        if not okay:
            return
        index = self.indexOf(browser)
        title = str(browser.title())
        tooltip = title
        if len(title) > 13:
            title = title[0:13] + '...'
        self.setTabText(index, title)
        self.setTabToolTip(index, tooltip)

    @pyqtSignature('')
    def closeTab(self):
        index = self.currentIndex()
        widget = self.widget(index)
        if widget:
            self.removeTab(index)
            widget.setAttribute(Qt.WA_DeleteOnClose)
            widget.close()

    @pyqtSignature('')
    def detachTab(self):
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
