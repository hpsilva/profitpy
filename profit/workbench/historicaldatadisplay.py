#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from itertools import ifilter

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QFrame, QIcon

from profit.lib import BasicHandler, makeCheckNames
from profit.lib.gui import ValueTableItem, symbolIcon
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
        self.histDataView.setModel(model)
        session.registerMeta(self)
