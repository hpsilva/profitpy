#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import QAbstractTableModel, QSize, QVariant, Qt
from PyQt4.QtGui import QFrame

from profit.lib import Signals, valueAlign
from profit.widgets.ui_accountdisplay import Ui_AccountDisplay


class AccountTableModel(QAbstractTableModel):
    """ Data model class for account messages.

    """
    columnTitles = ['Item', 'Currency', 'Value', 'Account', 'Plot']
    dataExtractors = {
        0:lambda m:m.key,
        1:lambda m:m.currency,
        2:lambda m:m.value,
        3:lambda m:m.accountName
    }
    alignments = {
        2:valueAlign,
        3:valueAlign,
        }

    def __init__(self, session, parent=None):
        """ Constructor.

        @param session Session instance
        @param parent ancestor object
        """
        QAbstractTableModel.__init__(self, parent)
        self.setSession(session)

    def setSession(self, session):
        """ Associates this model with a session.

        @param session Session instance
        @return None
        """
        self.session = session
        self.messageItems = items = {}
        self.messageIndex = indexed = []
        try:
            messages = session.typedMessages['UpdateAccountValue']
        except (KeyError, ):
            pass
        else:
            for mtime, message, mindex in messages:
                items[(message.key, message.currency)] = message
            indexed.extend(sorted(items.keys()))
            self.reset()
        session.registerMeta(self)

    def on_session_UpdateAccountValue(self, message):
        """ Signal handler for incoming execution details messages.

        @param message ExecDetails message instance
        @return None
        """
        key = (message.key, message.currency)
        items = self.messageItems
        try:
            items[key]
        except (KeyError, ):
            items[key] = message
            self.messageIndex = sorted(items.keys())
            self.emit(Signals.layoutChanged)
        else:
            items[key] = message
            row = self.messageIndex.index(key)
            self.emit(Signals.dataChanged,
                      self.createIndex(row, 0),
                      self.createIndex(row, 4))

    def data(self, index, role):
        """ Framework hook to determine data stored at index for given role.

        @param index QModelIndex instance
        @param role Qt.DisplayRole flags
        @return QVariant instance
        """
        if not index.isValid():
            return QVariant()
        row = index.row()
        col = index.column()
        key = self.messageIndex[row]
        message = self.messageItems[key]
        if role == Qt.TextAlignmentRole:
            try:
                val = QVariant(self.alignments[col])
            except (KeyError, ):
                val = QVariant()
            return val
        elif role != Qt.DisplayRole:
            return QVariant()
        try:
            val = QVariant(self.dataExtractors[col](message))
        except (KeyError, ):
            val = QVariant()
        return val

    def headerData(self, section, orientation, role):
        """ Framework hook to determine header data.

        @param section integer specifying header (e.g., column number)
        @param orientation Qt.Orientation value
        @param role Qt.DisplayRole flags
        @return QVariant instance
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.columnTitles[section])
        return QVariant()

    def rowCount(self, parent=None):
        """ Framework hook to determine data model row count.

        @param parent ignored
        @return number of rows (number of execution details messages)
        """
        return len(self.messageIndex)

    def columnCount(self, parent=None):
        """ Framework hook to determine data model column count.

        @param parent ignored
        @return number of columns (see columnTitles)
        """
        return len(self.columnTitles)


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
        self.accountValuesTable.verticalHeader().hide()
        self.setupModel(session)

    def setupModel(self, session):
        """ Configures this instance for a session.

        @param session Session instance
        @return None
        """
        self.session = session
        self.dataModel = AccountTableModel(session, self)
        self.accountValuesTable.setModel(self.dataModel)
