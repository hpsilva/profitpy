#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QFileDialog, QFrame, QInputDialog, QMessageBox

from profit.lib.core import Settings, Signals
from profit.widgets.settingsdialog import SysPathDialog
from profit.widgets.ui_strategydisplay import Ui_StrategyDisplay


class StrategyDisplay(QFrame, Ui_StrategyDisplay):
    def __init__(self, session, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.session = session
        self.settings = Settings()
        self.settings.beginGroup(Settings.keys.strategy)
        self.setupWidgets()

    def setupWidgets(self):
        wid = self.callableSelect
        wid.revertSource = \
            lambda :self.settings.value('source', '').toString()
        wid.saveSource = \
            lambda src:self.settings.setValue('source', src)
        getv = self.settings.value
        wid.basicSetup(
            callType=getv('typeindex', 0).toInt()[0],
            locationText=getv('location', '').toString(),
            sourceEditorText=getv('source', '').toString())

    @pyqtSignature('int')
    def on_callableType_currentIndexChanged(self, index):
        self.settings.setValue('typeindex', index)

    def on_callableLocation_textChanged(self, text):
        self.settings.setValue('location', text)
