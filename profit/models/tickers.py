#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import Qt, QModelIndex, QObject, QVariant, QString
from profit.lib import valueAlign
from profit.models import BasicItem, BasicItemModel


class TickersModel(BasicItemModel):
    """ Model for a collection of tickers.

    """
    def __init__(self, session=None, parent=None):
        BasicItemModel.__init__(self, TickersRootItem(), parent)
        self.symbolIcon = lambda x:None
        self.session = session
        if session is not None:
            session.registerMeta(self)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        item = index.internalPointer()
        column = index.column()
        data = QVariant()
        if role in (Qt.DecorationRole, Qt.ToolTipRole):
            data = QVariant(item[column])
        return data

    def findContract(self, contract):
        pass

    def findTicker(self, tickerId):
        tickerItems = self.invisibleRootItem.children
        try:
            return [item for item in tickerItems if item[0]==tickerId][0]
        except (IndexError, ):
            pass

    def on_session_TickPrice_TickSize(self, message):
        tickerId = message.tickerId
        item = self.findTicker(tickerId)
        if item:
            item.update(message)
        else:
            root = self.invisibleRootItem
            root.append(TickersItem.fromMessage(message, root))
            print '####', len(root.data), [i.toString() for i in root.data]
        self.reset()


class TickersItem(BasicItem):
    columnLookups = [
        ('Ticker Id', lambda msg:msg.tickerId),
        ('Field', lambda msg:msg.field),
        ('Price', lambda msg:msg.price),
        ('Size', lambda msg:msg.size),
        ('Can Auto Execute', lambda msg: msg.canAutoExecute),
    ]

    def __init__(self, data, parent=None, message=None):
        BasicItem.__init__(self, data, parent)
        self.message = message

    @classmethod
    def fromMessage(cls, message, parent):
        """ New instance from message values

        @param cls class object
        @param message ib.opt.message object
        @param parent parent of this item
        @return new instance of cls
        """
        values = []
        for label, lookup in cls.columnLookups:
            try:
                value = lookup(message)
            except (AttributeError, ):
                value = 0
            values.append(value)
        return cls(values, parent, message)

    def update(self, message):
        """ Update the item with values from a message.

        @param message ib.opt.message object
        @return None
        """
        for column, (label, lookup) in enumerate(self.columnLookups):
            try:
                self[column] = lookup(message)
            except (AttributeError, ):
                pass

class TickersRootItem(TickersItem):
    """ Tickers model item with automatic values (for horizontal headers).

    """
    def __init__(self):
        TickersItem.__init__(self, self.horizontalLabels())

    def horizontalLabels(self):
        """ Generates list of horizontal header values.

        """
        return map(QVariant, [label for label, lookup in self.columnLookups])
