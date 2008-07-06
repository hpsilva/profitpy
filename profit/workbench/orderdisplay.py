#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from itertools import ifilter

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QFrame

from profit.lib.core import SessionHandler, nameIn
from profit.workbench.widgets.ui_orderdisplay import Ui_OrderDisplay


def replayOrders(messages, obj):
    ismsg = nameIn('OpenOrder', 'OrderStatus')
    def pred((t, m)):
        return ismsg(m)
    for time, message in ifilter(pred, messages):
        call = getattr(obj, 'on_session_%s' % message.typeName)
        call(message)


class OrderDisplay(QFrame, Ui_OrderDisplay, SessionHandler):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.orderItems = {}
        self.orderTable.verticalHeader().hide()
        self.requestSession()

    def setSession(self, session):
        self.session = session
        replayOrders(session.messages, self)
        session.registerMeta(self)

    def on_session_OrderStatus(self, message):
        orderId = message.orderId
        try:
            items = self.orderItems[orderId]
        except (KeyError, ):
            print '### warning:  order items not found on status for', orderId
            return
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
        table = self.orderTable
        contract = message.contract
        order = message.order
        orderId = order.m_orderId
        try:
            items = self.orderItems[orderId]
        except (KeyError, ):
            items = self.orderItems[orderId] = table.newItemsRow()
            table.resizeRowsToContents()
        items[0].setText(str(orderId))
        items[1].setSymbol(contract.m_symbol) # OK
        items[2].setText(order.m_totalQuantity) # OK
        #items[3].setText('') # active
        items[4].setText(order.m_action) # OK
        items[5].setText(order.m_orderType) # OK
        items[6].setText(order.m_lmtPrice) # OK
        items[7].setText(order.m_auxPrice) # OK
        items[8].setText(order.m_openClose) # OK
        #items[9].setText('') # filled
        #items[10].setText('') # remaining
        for col in [0, 2, 6, 7, 9, 10, 11, 12, 13, 14, 15]:
            items[col].setValueAlign()
