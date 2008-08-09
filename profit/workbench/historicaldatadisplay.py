#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtGui import QFrame
from profit.lib import BasicHandler
from profit.lib.gui import symbolIcon
from profit.workbench.widgets.ui_historicaldatadisplay import Ui_HistoricalDataDisplay


class HistoricalDataDisplay(QFrame, Ui_HistoricalDataDisplay, BasicHandler):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.requestSession()

    def setSession(self, session):
        self.session = session
        model = session.models.histdata
        model.symbolIcon = symbolIcon
        view = self.requestsView
        view.verticalHeader().hide()
        view.setModel(model)
        session.registerMeta(self)


    def on_requestsView_doubleClicked(self, index):
        if not index.isValid():
            return
        reqId = index.internalPointer()[0]
        print '##', reqId



    def createTab(self, requestId):
        pass

