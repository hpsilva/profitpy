#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import Qt, QUrl, QVariant
from PyQt4.QtGui import QAction, QBrush, QColor, QDesktopServices, QIcon, QMessageBox
from PyQt4.QtGui import QPixmap, QTableWidgetItem, QStandardItem

from profit.lib.core import DataRoles, Signals, valueAlign


class ValueColorItem(object):
    increase = QBrush(QColor(Qt.darkGreen))
    neutral = QBrush(QColor(Qt.blue))
    decrease = QBrush(QColor(Qt.red))
    compMap = {1:increase, -1:decrease, 0:neutral}

    @classmethod
    def setColors(cls, increase, neutral, decrease):
        cls.increase = QBrush(increase)
        cls.neutral = QBrush(neutral)
        cls.decrease = QBrush(decrease)


class ValueTableItem(QTableWidgetItem, ValueColorItem):
    """ Table item that changes colors based on value changes.

    """
    def __init__(self):
        """ Constructor.

        """
        QTableWidgetItem.__init__(self, self.UserType)
        self.setFlags(self.flags() & ~Qt.ItemIsEditable)
        self.value = None

    def setValue(self, value):
        """ Sets value of item and updates text color (if possible).

        @param string or number to set
        @return None
        """
        try:
            value = float(value)
        except (ValueError, ):
            self.setText(value)
            return
        current = self.value
        if current is None:
            self.value = value
            self.setText(str(value))
            return
        if value < current:
            self.setForeground(self.decrease)
        elif value > current:
            self.setForeground(self.increase)
        else:
            self.setForeground(self.neutral)
        self.value = value
        self.setText(str(value))

    def setSymbol(self, symbol):
        """ Sets the text and icon for a symbol-based item.

        @param symbol ticker symbol as string
        @return None
        """
        icon = symbolIcon(symbol)
        self.setIcon(icon)
        self.setText(symbol)

    def setValueAlign(self, alignment=valueAlign):
        """ Sets the text alignment of this item.

        @param alignment Qt alignment flags
        @return None
        """
        self.setTextAlignment(alignment)

    def setText(self, text):
        QTableWidgetItem.setText(self, str(text))


def colorIcon(color, width=10, height=10):
    """ Creates an icon filled with specified color.

    @param color QColor instance
    @param width width of icon in pixels
    @param height of icon in pixels
    @return QIcon instance
    """
    pixmap = QPixmap(width, height)
    pixmap.fill(color)
    return QIcon(pixmap)


def symbolIcon(symbol):
    """ Icon for a symbol.

    @param symbol name of symbol
    @return QIcon instance; transparent but valid if symbol icon not found
    """
    icon = QIcon(':images/tickers/%s.png' % (symbol.lower(), ))
    if icon.pixmap(16,16).isNull():
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 0, 0, 0))
        icon = QIcon(pixmap)
    return icon


def warningBox(title, text):
    return QMessageBox.warning(None, title, text, QMessageBox.Close)


def complementColor(c):
    hx = str(c.name())[1:]
    comp = ['%.2X' % (255 - int(a, 16)) for a in (hx[0:2], hx[2:4], hx[4:6])]
    return QColor('#' + str.join('', comp))


def separator():
    sep = QAction(None)
    sep.setSeparator(True)
    return sep


class UrlAction(QAction):
    def __init__(self, text, url, tooltip=None, parent=None):
        QAction.__init__(self, text, parent)
        self.setData(QVariant(url))
        self.setToolTip(tooltip or text)


class UrlRequestor(object):
    """ Mixin that provides method for initial handling of requests to open a URL.

    Object instances must have a settings member.
    """
    def on_urlAction(self, action):
        url = action.data().toString()
        settings = self.settings
        settings.beginGroup(settings.keys.main)
        useExternal = settings.value('useSystemBrowser', False).toBool()
        settings.endGroup()
        if useExternal:
            QDesktopServices.openUrl(QUrl(url))
        else:
            value = QStandardItem(url)
            value.setData(QVariant(url), DataRoles.url)
            self.emit(Signals.openUrl, value)
