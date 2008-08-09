#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from sys import platform

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import QTabWidget

from profit.lib import Signals
from profit.lib.gui import addCloseAction
from profit.lib.widgets.buttons import CloseTabButton, DetachTabButton


class LocalTabWidget(QTabWidget):
    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        self.closeTabButton = CloseTabButton(self)
        self.detachTabButton = DetachTabButton(self)
        self.setCornerWidget(self.closeTabButton, Qt.TopRightCorner)
        self.setCornerWidget(self.detachTabButton, Qt.TopLeftCorner)
        connect = self.connect
        connect(self.closeTabButton, Signals.clicked, self.closeTab)
        connect(self.detachTabButton, Signals.clicked, self.detachTab)

    def closeTab(self):
        """ Closes the current tab.

        """
        index = self.currentIndex()
        widget = self.widget(index)
        if widget:
            self.removeTab(index)
            widget.setAttribute(Qt.WA_DeleteOnClose)
            widget.close()

    def closeTabs(self):
        """ Closes all tabs.

        """
        while self.currentIndex() != -1:
            self.closeTab()

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
