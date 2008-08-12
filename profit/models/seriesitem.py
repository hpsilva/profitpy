#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import Qt, QModelIndex, QVariant, QString
from profit.lib import maybeFloat, valueAlign
from profit.models import BasicItem, BasicItemModel


class SeriesItemModel(BasicItemModel):
    """

    """
    def __init__(self, session=None, parent=None):
        BasicItemModel.__init__(self, RootSeriesItem(), parent)
        self.session = session
        if session is not None:
            session.registerMeta(self)

    def data(self, index, role):
        """

        """
        if not index.isValid():
            return QVariant()
        item = index.internalPointer()
        data = QVariant()
        column = index.column()
        if role == Qt.DisplayRole:
            data = item[column]
        elif role == Qt.ToolTipRole:
            data = item[column]
        elif role == Qt.DecorationRole and column==0:
            data = item.colorIcon()
        elif role == Qt.CheckStateRole and column==0 and item.checkable:
            data = item.checked
        elif role in (Qt.TextAlignmentRole, ):
            data = maybeFloat(item[column], Qt.AlignRight|Qt.AlignVCenter)
        return QVariant(data)


    def flags(self, index):
        if not index.isValid():
            return QVariant()
        item = index.internalPointer()
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if item.column==0 and item.checkable:
            flags |= Qt.ItemIsEditable | Qt.ItemIsUserCheckable
        return flags

    def findItem(self, key):
        """ Returns the item for the given contract, or None.

        """
        items = self.invisibleRootItem.children
        try:
            return [i for i in items if i.message.key==key][0]
        except (IndexError, ):
            pass


class SeriesItem(BasicItem):
    """ Base class for items in the account model.

    """
    columnLookups = [
        ('Series', lambda x:x.key),
        ('Value', lambda x:x.value),
    ]

    def __init__(self, data, parent=None):
        BasicItem.__init__(self, data, parent)
        self.checkable = False
        self.checked = False
        self.color = None
        self.curve = None


class RootSeriesItem(SeriesItem):
    """ SeriesItem model item with automatic values (for horizontal headers).

    """
    def __init__(self):
        SeriesItem.__init__(self, self.horizontalLabels())

    def horizontalLabels(self):
        """ Generates list of horizontal header values.

        """
        return map(QVariant, [label for label, lookup in self.columnLookups])
