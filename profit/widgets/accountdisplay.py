#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import QAbstractTableModel, QSize, QVariant, Qt
from PyQt4.QtGui import QFrame, QStandardItemModel, QStandardItem

from profit.lib.core import SessionHandler, Signals, valueAlign
from profit.lib.gui import colorIcon, complementColor
from profit.series import Series
from profit.widgets.plot import PlotCurve, ControlTreeValueItem
from profit.widgets.ui_accountdisplay import Ui_AccountDisplay


class AccountTableModel(QStandardItemModel):
    columnTitles = ['Item', 'Currency', 'Value', 'Account',]

    def __init__(self, session, parent=None):
        QStandardItemModel.__init__(self, parent)
        self.setHorizontalHeaderLabels(self.columnTitles)
        self.items = {}
        self.session = session
        try:
            messages = session.typedMessages['UpdateAccountValue']
        except (KeyError, ):
            pass
        else:
            slot = self.on_session_UpdateAccountValue
            for mrec in messages:
                slot(mrec[1])
        session.registerMeta(self)

    def on_session_UpdateAccountValue(self, message):
        key = (message.key, message.currency, message.accountName)
        try:
            items = self.items[key]
        except (KeyError, ):
            pass
        else:
            items[2].setText(message.value)


class AccountDisplay(QFrame, Ui_AccountDisplay, SessionHandler):
    """ Table view of an account.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor object
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.requestSession()

    def setSession(self, session):
        """ Configures this instance for a session.

        @param session Session instance
        @return None
        """
        self.session = session
        self.dataModel = model = AccountTableModel(session, self)
        plot = self.plot
        plot.plotButton.setVisible(False)
        plot.setSessionPlot(session, session.accountCollection, 'account')
        plot.controlsTreeModel = model
        plot.controlsTree.setModel(model)
        plot.controlsTree.header().show()
        for key, series in session.accountCollection.data.items():
            self.newPlotSeries(
                key, series, session.accountCollection.last.get(key, None))
        connect = self.connect
        connect(session, Signals.createdAccountData, self.newPlotSeries)
        connect(
            model, Signals.standardItemChanged,
            plot.on_controlsTree_itemChanged)
        connect(model, Signals.rowsInserted, self.modelRowsInserted)
        plot.loadSelections()

    def newPlotSeries(self, key, series, value):
        cols = range(len(self.dataModel.columnTitles))
        items = [ControlTreeValueItem('') for i in cols[1:]]
        items[0].setText(key[1])
        items[1].setText(str(value))
        items[2].setText(key[2])
        item = self.plot.addSeries(key, series, items=items)

    def modelRowsInserted(self, parent, start, end):
        model = self.dataModel
        item = model.itemFromIndex(parent)
        if item:
            others = [model.item(item.row(), i) for i in range(1,4)]
            key = tuple(str(i.text()) for i in (item, others[0], others[2]))
            model.items[key] = [item, ] + others
