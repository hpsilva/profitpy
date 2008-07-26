#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from itertools import ifilter

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QFrame

from profit.lib import SessionHandler, nameIn
from profit.workbench.widgets.ui_orderdisplay import Ui_OrderDisplay

## TODO: orders should be displayed in a parent/child relationship,
## with the OpenOrder message as the parent and the related
## OrderStatus messages as children.


def replayOrderMessages(messages, openOrder, orderStatus):
    """

    """
    ismsg = nameIn('OpenOrder', 'OrderStatus')
    calls = {'OpenOrder':openOrder, 'OrderStatus':orderStatus}
    def pred((t, m)):
        return ismsg(m)
    for time, message in ifilter(pred, messages):
        calls[message.typeName](message)


class OrderDisplay(QFrame, Ui_OrderDisplay, SessionHandler):
    """ OrderDisplay -> table of orders

    """
    def __init__(self, parent=None):
        """ Initializer.

        @param parent ancestor of this object
        """
        QFrame.__init__(self, parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.orderItems = {}
        self.orderTable.verticalHeader().hide()
        self.requestSession()

    def setSession(self, session):
        """ Configures this instance for a session.

        @param session Session instance
        @return None
        """
        self.session = session
        replayOrderMessages(
            session.messages,
            self.on_session_OpenOrder,
            self.on_session_OrderStatus,
        )
        session.registerMeta(self)

    def on_session_OrderStatus(self, message):
        orderId = message.orderId
        items = self.getTableRowItems(orderId)
        table = self.orderTable
        items[3].setText(message.status)
        items[9].setText(message.filled)
        items[10].setText(message.remaining)
        items[11].setText(message.avgFillPrice)
        items[12].setText(message.lastFillPrice)
        items[13].setText(message.parentId)
        items[14].setText(message.clientId)
        items[15].setText(message.permId)
        table.resizeColumnsToContents()

    def on_session_OpenOrder(self, message):
        order = message.order
        orderId = order.m_orderId
        items = self.getTableRowItems(orderId)
        contract = message.contract
        items[0].setText(str(orderId))
        items[1].setSymbol(contract.m_symbol)
        items[2].setText(order.m_totalQuantity)
        #items[3].setText('') # active
        items[4].setText(order.m_action)
        items[5].setText(order.m_orderType)
        items[6].setText(order.m_lmtPrice)
        items[7].setText(order.m_auxPrice)
        items[8].setText(order.m_openClose)
        #items[9].setText('') # filled
        #items[10].setText('') # remaining
        for col in [0, 2, 6, 7, 9, 10, 11, 12, 13, 14, 15]:
            items[col].setValueAlign()

    def makeTableRowItems(self, orderId):
        table = self.orderTable
        items = self.orderItems[orderId] = table.newItemsRow()
        table.resizeRowsToContents()
        return items

    def getTableRowItems(self, orderId):
        try:
            items = self.orderItems[orderId]
        except (KeyError, ):
            items = self.makeTableRowItems(orderId)
        return items

