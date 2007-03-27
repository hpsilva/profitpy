#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import QAbstractTableModel, QSize, QVariant, Qt
from PyQt4.QtGui import QFrame, QStandardItemModel, QStandardItem

from profit.lib.core import Signals, valueAlign
from profit.series import Series
from profit.widgets.plot import PlotCurve
from profit.widgets.ui_accountdisplay import Ui_AccountDisplay


class AccountModelItem(QStandardItem):
    def __init__(self, name=False):
        QStandardItem.__init__(self)
        self.setEditable(False)
        self.name = lambda :name
        if name:
            self.curve = PlotCurve(name)
            self.data = Series()

    def isChecked(self):
        return self.checkState() == Qt.Checked


class AccountTableModel(QStandardItemModel):
    columnTitles = ['Item', 'Currency', 'Value', 'Account',]

    def __init__(self, session, parent=None):
        QStandardItemModel.__init__(self, parent)
        self.setHorizontalHeaderLabels(self.columnTitles)
        self.items = {}
        self.bareItems = []
        self.setSession(session)

    def setSession(self, session):
        """ Associates this model with a session.

        @param session Session instance
        @return None
        """
        self.session = session
        try:
            messages = session.typedMessages['UpdateAccountValue']
        except (KeyError, ):
            pass
        else:
            for mtime, message, mindex in messages:
                self.on_session_UpdateAccountValue(message)
            self.reset()
        session.registerMeta(self)

    def on_session_UpdateAccountValue(self, message):
        key = (message.key, message.currency)
        row = self.rowCount()
        colcount = len(self.columnTitles)
        try:
            items = self.items[key]
            row = items[0].row()
        except (KeyError, ):
            t = '/'.join(key)
            self.insertRow(row, [AccountModelItem(t), ] + \
                                [AccountModelItem() for i in
                                 range(colcount-1)])
            items = \
                  self.items[key] = \
                      [self.item(row, i) for i in range(colcount)]
            self.bareItems.append(items[0])
            self.emit(Signals.layoutChanged)
        items[0].setText(message.key)
        items[1].setText(message.currency)
        items[2].setText(message.value)
        items[3].setText(message.accountName)
        try:
            value = float(message.value)
            items[0].setCheckable(True)
            items[0].data.append(value)
        except (Exception, ):
            pass
        self.emit(Signals.dataChanged,
                  self.createIndex(row, 0),
                  self.createIndex(row, 4))


class AccountDisplay(QFrame, Ui_AccountDisplay):
    """ Table view of an account.

    """
    def __init__(self, session, parent=None):
        """ Constructor.

        @param session Session instance
        @param parent ancestor object
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.setupModel(session)

    def setupModel(self, session):
        """ Configures this instance for a session.

        @param session Session instance
        @return None
        """
        self.session = session
        self.dataModel = AccountTableModel(session, self)
        self.plot.controlsTreeModel = self.dataModel
        self.plot.controlsTree.setModel(self.dataModel)
        self.plot.controlsTreeItems = self.dataModel.bareItems
        self.connect(self.dataModel, Signals.standardItemChanged,
                     self.plot.on_controlsTree_itemChanged)

