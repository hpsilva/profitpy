#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import Qt, QModelIndex, QObject, QAbstractTableModel, QVariant, QAbstractItemModel
from profit.lib.core import Signals


class ListStorage(QObject):
    def __init__(self, parent):
        QObject.__init__(self, parent)
        self.storage = []

    def __contains__(self, item):
        return item in self.storage

    def __getitem__(self, index):
        return self.storage[index]

    def __setitem__(self, index, value):
        self.storage[index] = value

    def __str__(self):
        return str(self.storage)

    def __len__(self):
        return len(self.storage)

    def append(self, item):
        self.storage.append(item)


class BasicModelMixin(object):
    horizontalLabels = []
    verticalLabels = []
    sessionResendSignals = []

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if (orientation == Qt.Horizontal) and (role == Qt.DisplayRole):
            return QVariant(self.horizontalLabels[section])
        elif (orientation == Qt.Vertical) and (role == Qt.DisplayRole):
            return QVariant(self.verticallabels[section])
        return QVariant()

    def columnCount(self, parent=QModelIndex()):
        return len(self.horizontalLabels)

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self)


class BasicModel(QAbstractItemModel, BasicModelMixin):
    def __init__(self, parent=None):
        QAbstractItemModel.__init__(self, parent)


class BasicTableModel(QAbstractTableModel, BasicModelMixin):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)

