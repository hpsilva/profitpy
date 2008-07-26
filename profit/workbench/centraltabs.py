#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from functools import partial
from sys import platform

from PyQt4.QtCore import QTimer, QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QIcon, QTabWidget, QStandardItem

from profit.lib import importItem, logging
from profit.lib import SessionHandler, Signals, DataRoles, instance
from profit.lib.gui import addCloseAction, makeUrlItem
from profit.lib.widgets.buttons import CloseTabButton, DetachTabButton
from profit.lib.widgets.webbrowser import WebBrowserDisplay
from profit.workbench.tickerplotdisplay import TickerPlotDisplay


class CentralTabs(QTabWidget, SessionHandler):
    """ CentralTabs -> tab widget with special powers

    """
    def __init__(self, parent=None):
        """ Initializer.

        @param parent ancestor of this widget
        """
        QTabWidget.__init__(self, parent)
        self.closeTabButton = CloseTabButton(self)
        self.detachTabButton = DetachTabButton(self)
        self.setCornerWidget(self.closeTabButton, Qt.TopRightCorner)
        self.setCornerWidget(self.detachTabButton, Qt.TopLeftCorner)
        app, connect = instance(), self.connect
        connect(app, Signals.sessionItemActivated, self.createTab)
        connect(app, Signals.openUrl, self.createTab)
        connect(app, Signals.tickerClicked, self.createTab)
        connect(self.closeTabButton, Signals.clicked, self.closeTab)
        connect(self.detachTabButton, Signals.clicked, self.detachTab)
        self.requestSession()

    def createTab(self, value):
        """ Create or display a tab from a value

        @param value string or model item
        @return None
        """
        hs = [self.createBrowserTab, self.createTickerPlotTab, self.createDisplayTab]
        for handler in hs:
            try:
                if handler(value):
                    break
            except (Exception, ), exc:
                logging.debug("Exception (debug): %r:%s (h:%s)", exc, exc, handler, )

    def createBrowserTab(self, item):
        """ Creates a new web browser tab.

        @param value string or model item
        @return True if display widget created, otherwise None
        """
        if isinstance(item, (basestring, )):
            item = makeUrlItem(item)
        if item.data(DataRoles.url).isValid():
            url = item.data(DataRoles.url).toString()
            title = item.data(DataRoles.urlTitle).toString()
            widget = WebBrowserDisplay(self)
            widget.basicConfig(url)
            index = self.addTab(widget, title)
            icon = item.icon()
            if icon.isNull():
                icon = QIcon(":/images/icons/www.png")
            self.setTextIconCurrentTab(index, title, icon)
            loadHandler = partial(self.resetBrowserTab, browser=widget)
            self.connect(widget, Signals.loadFinished, loadHandler)
            return True

    def createTickerPlotTab(self, item):
        """ Creates or displays a ticker plot tab.

        @param value string or model item
        @return True if display widget created, otherwise None
        """
        tickerId, tickerIdValid = item.data(DataRoles.tickerId).toInt()
        symbol = str(item.data(DataRoles.tickerSymbol).toString())
        if tickerIdValid and self.setCurrentLabel(symbol):
            return True
        if tickerIdValid:
            widget = TickerPlotDisplay(self)
            session = self.session
            widget.setSessionPlot(session, session.dataMaps.ticker, tickerId)
            index = self.addTab(widget, symbol)
            icon = QIcon(item.data(Qt.DecorationRole))
            self.setTextIconCurrentTab(index, symbol, icon)
            return True

    def createDisplayTab(self, item):
        """ Creates or displays a name-based display.

        @param value string or model item
        @return True if display widget created, otherwise None
        """
        text = str(item.data().toString())
        if self.setCurrentLabel(text):
            return True
        name = str(item.data(DataRoles.displayImportName).toString())
        if name:
            cls = importItem(name)
            widget = cls(self)
            index = self.addTab(widget, text)
            icon = QIcon(item.data(Qt.DecorationRole))
            self.setTextIconCurrentTab(index, text, icon)
            return True

    def pageMap(self):
        """ Makes a mapping like {'connection':1, 'account':3, ...}

        @return mapping of tab name to tab index
        """
        return dict([(str(self.tabText(i)), i) for i in range(self.count())])

    def closeTab(self):
        """ Closes the current tab tab.

        @return None
        """
        index = self.currentIndex()
        widget = self.widget(index)
        if widget:
            self.removeTab(index)
            widget.setAttribute(Qt.WA_DeleteOnClose)
            widget.close()

    def detachTab(self):
        """ Deatches the current tab and makes it a top-level window.

        @return None
        """
        index = self.currentIndex()
        text = str(self.tabText(index))
        widget = self.widget(index)
        widget.setWindowIcon(self.tabIcon(index))
        try:
            widget.setWindowTitle(str(widget.windowTitle()) % text)
        except (TypeError, ):
            pass
        addCloseAction(widget)
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
        """ Reconfigures a tab based on a web browser widget state.

        @param okay True if browser page load is finished
        @keyparam browser=None WebBrowserDispay object
        @return None
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
        """ Sets tab text and icon, and makes tab current.

        @param index index of tab to modify and display
        @param text text for tab
        @param icon icon for tab
        @return None
        """
        self.setTabText(index, text)
        self.setTabIcon(index, icon)
        self.setCurrentIndex(index)

    def setCurrentLabel(self, label):
        """ Sets current tab by name if possible.

        @param label text of tab to make current
        @return True if successful, otherwise None
        """
        index = self.pageMap().get(label)
        if index is not None:
            self.setCurrentIndex(index)
            return True
