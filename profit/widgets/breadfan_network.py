#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

import sys

from PyQt4.QtCore import Qt, QVariant
from PyQt4.QtGui import (QApplication, QFrame, QIcon,
                         QStandardItem, QStandardItemModel, QToolBar)

from profit.lib.core import SessionHandler
from profit.lib.core import Signals, tickerIdRole
from profit.widgets.ui_breadfan_network import Ui_BreadFanNetworkTree


class NetworkTreeItem(QStandardItem):
    """ Network tree item.

    """
    iconNameMap = {
        'account':'identity',
        'connection':'server',
        'messages':'view_text',
        'orders':'klipper_dock',
        'portfolio':'bookcase',
        'strategy':'services',
        'tickers':'view_detailed',
    }

    def __init__(self, text):
        """ Constructor.

        @param text value for item display
        """
        QStandardItem.__init__(self, text)
        self.setEditable(False)
        self.setIcon(self.lookupIcon(text))
        hint = self.sizeHint()
        hint.setHeight(20)
        self.setSizeHint(hint)

    def lookupIcon(self, key):
        """ Locates icon for given key.

        @param key item text
        @return QIcon instance
        """
        try:
            name = self.iconNameMap[key]
            icon = QIcon(':images/icons/%s.png' % name)
        except (KeyError, ):
            style = QApplication.style()
            icon = style.standardIcon(style.SP_DirIcon)
        return icon


class NetworkTreeModel(QStandardItemModel):
    
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor object
        """
        QStandardItemModel.__init__(self)
        root = self.invisibleRootItem()
        session = {'foo':[1, 2, 3], 'bar':[2, 4, 6]}
        for key, values in session.items():
            item = NetworkTreeItem(key)
            root.appendRow(item)
            for value in values:
                subitem = NetworkTreeItem(str(value))
                item.appendRow(subitem)


class BreadFanNetworkTree(QFrame, Ui_BreadFanNetworkTree):
    """ Tree view of a BreadFan network config.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor of this widget
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
