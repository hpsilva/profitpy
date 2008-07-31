#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from itertools import ifilter

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QFrame, QIcon

from profit.lib import BasicHandler, makeCheckNames
from profit.lib.gui import ValueTableItem
from profit.workbench.widgets.ui_historicaldatadisplay import Ui_HistoricalDataDisplay


def replayHistoricalData(messages, callback):
    isHistMessage = makeCheckNames('HistoricalData')
    def pred((t, m)):
        return isHistMessage(m)
    for time, message in ifilter(pred, reversed(messages)):
        callback(message)


class HistoricalDataDisplay(QFrame, Ui_HistoricalDataDisplay, BasicHandler):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.requestSession()

    def setSession(self, session):
        self.session = session
        replayHistoricalData(session.messages, self.on_session_HistoricalData)
        session.registerMeta(self)


    def on_session_HistoricalData(self, message):
        pass
