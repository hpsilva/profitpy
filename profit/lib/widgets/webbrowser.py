#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import pyqtSignature, QEvent, QObject, Qt, QUrl
from PyQt4.QtGui import QWidget

from profit.lib.core import Signals
from profit.lib.widgets.ui_webbrowser import Ui_WebBrowserDisplay


class EnterKeyFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Enter:
                self.emit(Signals.textChanged, self.parent().urlEdit.text())
        return False


class WebBrowserDisplay(QWidget, Ui_WebBrowserDisplay):
    """

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor of this widget
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)

    def basicConfig(self, url):
        self.urlEdit.setText(url)
        self.webView.load(QUrl(url))
        self.connect(self.webView, Signals.loadFinished, self.setWebLocation)
        self.connect(self.webView, Signals.loadFinished, self, Signals.loadFinished)
        self.filtr = EnterKeyFilter(self)
        self.connect(self.filtr, Signals.textChanged, self.loadUrlString)

        self.urlEdit.installEventFilter(self.filtr)

    def loadUrlString(self, text):
        print '### new url', text
        self.webView.load(QUrl(text))

    def setWebLocation(self, okay):
        if okay:
            self.urlEdit.setText(self.webView.url().toString())

    def title(self):
        return self.webView.title()

    @pyqtSignature('')
    def on_reloadButton_clicked(self):
        self.reloadButton.setEnabled(False)
        self.stopButton.setEnabled(True)

    @pyqtSignature('')
    def on_stopButton_clicked(self):
        self.reloadButton.setEnabled(True)
        self.stopButton.setEnabled(False)

