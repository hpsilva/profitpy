#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from time import strftime, strptime

from PyQt4.QtCore import QAbstractTableModel, QVariant, Qt
from PyQt4.QtGui import QFrame

from profit.lib.core import SessionHandler, Signals, Slots, nameIn, valueAlign
from profit.lib.gui import symbolIcon
from profit.workbench.widgets.ui_executionsdisplay import Ui_ExecutionsDisplay


dayFormatOut = '%a %d %b %Y'
dayFormatIn = '%Y%m%d'


def messageDate(message):
    """ Extracts and formats the date from an execution details message.

    @param message message instance
    @return formatted date as string
    """
    datetime = message.execution.m_time
    datepart = datetime.split()[0]
    return strftime(dayFormatOut, strptime(datepart, dayFormatIn))


def messageTime(message):
    """ Extracts the time from an execution details message.

    @param message message instance
    @return time as string
    """
    datetime = message.execution.m_time
    timepart = datetime.split()[1]
    return timepart


class ExecutionsTableModel(QAbstractTableModel):
    """ Data model for execution details messages table.

    """
    columnTitles = [
        'Action', 'Quantity', 'Underlying', 'Price', 'Currency',
        'Exchange', 'Date', 'Time', 'Id', 'Order Reference',
    ]
    dataExtractors = {
        0:lambda m:m.execution.m_side,
        1:lambda m:m.execution.m_shares,
        2:lambda m:m.contract.m_symbol,
        3:lambda m:m.execution.m_price,
        4:lambda m:m.contract.m_currency,
        5:lambda m:m.execution.m_exchange,
        6:messageDate,
        7:messageTime,
        8:lambda m:m.execution.m_permId,
        9:lambda m:m.execution.m_orderId,
    }
    alignments = {
        1:valueAlign,
        3:valueAlign,
        6:valueAlign,
        7:valueAlign,
        8:valueAlign,
        9:valueAlign,
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
        ismsg = nameIn('ExecDetails')
        msgs = enumerate((msg for time, msg in session.messages))
        self.messageIndexes = [idx for idx, msg in msgs if ismsg(msg)]
        self.session = session
        self.messages = session.messages
        session.registerMeta(self)

    def on_session_ExecDetails(self, message):
        """ Signal handler for incoming execution details messages.

        @param message ExecDetails message instance
        @return None
        """
        self.messageIndexes.append(self.session.messagesBare.index(message))
        self.emit(Signals.layoutChanged)

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
        msgindex = self.messageIndexes[row]
        mtime, message = self.messages[msgindex]
        if role == Qt.DecorationRole and col == 2:
            return QVariant(symbolIcon(message.contract.m_symbol))
        elif role == Qt.TextAlignmentRole:
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
        return len(self.messageIndexes)

    def columnCount(self, parent=None):
        """ Framework hook to determine data model column count.

        @param parent ignored
        @return number of columns (see columnTitles)
        """
        return len(self.columnTitles)


class ExecutionsDisplay(QFrame, Ui_ExecutionsDisplay, SessionHandler):
    """ Combines a search filter bar (not working) and an exec details table.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor object
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.requestSession()
        self.executionsTable.verticalHeader().hide()

    def setSession(self, session):
        """ Configures this instance for a session.

        @param session Session instance
        @return None
        """
        self.session = session
        try:
            model = session.executionsDisplayModel
        except (AttributeError, ):
            model = session.executionsDisplayModel = \
                    ExecutionsTableModel(session)
        self.executionsTable.setModel(model)
        session.register(self.executionsTable, 'ExecDetails',
                         Slots.scrollToBottom)
