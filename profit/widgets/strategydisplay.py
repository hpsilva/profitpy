#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QFileDialog, QFrame, QInputDialog, QMessageBox

from profit.lib.core import Settings, Signals
from profit.lib.gui import SessionHandler
from profit.widgets.settingsdialog import SysPathDialog
from profit.widgets.ui_strategydisplay import Ui_StrategyDisplay


class StrategyDisplay(QFrame, Ui_StrategyDisplay, SessionHandler):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.settings = Settings()
        self.settings.beginGroup(Settings.keys.strategy)
        self.setupWidgets()
        self.requestSession()

    def setupWidgets(self):
        def revert():
            return self.settings.value('source', '').toString()
        def save(src):
            self.settings.setValue('source', src)
        getv = self.settings.value
        self.callableSelect.basicSetup(
            callType=getv('typeindex', 0).toInt()[0],
            locationText=getv('location', '').toString(),
            sourceEditorText=getv('source', '').toString(),
            revertSource=revert,
            saveSource=save)

    @pyqtSignature('int')
    def on_callableType_currentIndexChanged(self, index):
        self.settings.setValue('typeindex', index)

    def on_callableLocation_textChanged(self, text):
        self.settings.setValue('location', text)
