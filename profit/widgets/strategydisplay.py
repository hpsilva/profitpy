#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QFrame, QIcon, QMessageBox

from profit.lib.core import Settings, Signals
from profit.lib.gui import SessionHandler
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
            callType=getv('type', '').toString(),
            locationText=getv('location', '').toString(),
            sourceEditorText=getv('source', '').toString(),
            revertSource=revert,
            saveSource=save,
            disableFactoryType=True)

    def setSession(self, session):
        self.session = session
        self.strategy = session.strategy
        self.connect(
            self.strategy, Signals.strategyEnabled, self.on_strategy_enabled)
        self.on_strategy_enabled(session.strategy.enabled)

    def on_strategy_enabled(self, status):
        self.callableGroup.setDisabled(status)
        icofs = ':/images/icons/connect_%s.png'
        buttonitems = {
            True:[('Active.  Click to Deactivate', icofs % 'established'), ],
            False:[('Inactive.  Click to Activate.', icofs % 'no'), ],
        }
        for text, icon in buttonitems[status]:
            self.statusButton.setText(text)
            self.statusButton.setIcon(QIcon(icon))

    @pyqtSignature('int')
    def on_callableType_currentIndexChanged(self, index):
        self.settings.setValue(
            'type', self.callableSelect.callableType.itemData(index))

    def on_callableLocation_textChanged(self, text):
        self.settings.setValue('location', text)

    @pyqtSignature('')
    def on_statusButton_clicked(self):
        settings = Settings()
        settings.beginGroup(Settings.keys.main)
        confirm = settings.value('confirmActivateStrategy', True).toBool()
        if confirm and not self.strategy.enabled:
            mb = QMessageBox
            if mb.question(self,
                'Activate Trading Strategy?',
                'Do you really want to activate your trading strategy?',
                mb.Yes|mb.No) != mb.Yes:
                return
        self.strategy.enabled = not self.strategy.enabled
