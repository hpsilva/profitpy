#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

import logging

from PyQt4.QtCore import Qt, pyqtSignature
from PyQt4.QtGui import QFrame, QIcon, QMessageBox

from profit.lib.core import SessionHandler, Settings, Signals
from profit.widgets.ui_strategytree import Ui_StrategyTree


class StrategyTree(QFrame, Ui_StrategyTree, SessionHandler):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.settings = Settings()
        self.settings.beginGroup(Settings.keys.strategy)
        self.setupWidgets()
        self.requestSession()

    def setupWidgets(self):
        getv = self.settings.value
        edit = self.callableSelect
        edit.basicSetup(
            callType=getv('type', '').toString(),
            locationText=getv('location', '').toString(),
            sourceEditorText=getv('source', '').toString(),
            revertSource=lambda :self.settings.value('source', '').toString(),
            saveSource=lambda src:self.settings.setValue('source', src),
            disableFactoryType=True)
        logging.debug("strategyTree editor CONNECT")
        self.connect(edit, Signals.modified, self.on_callableSelect_modified)

    def setSession(self, session):
        self.session = session
        self.strategy = strat = session.strategy
        self.on_strategy_activated(strat.active)
        self.on_strategy_loaded(strat.loadMessage)
        connect = self.connect
        connect(strat, Signals.strategyActivated, self.on_strategy_activated)
        connect(strat, Signals.strategyLoaded, self.on_strategy_loaded)
        connect(strat, Signals.strategyLoadFailed, self.on_strategy_loadfail)

    def on_strategy_activated(self, status):
        if status:
            msg = 'Strategy is active.  Click to deactivate it.'
            ico = 'established'
        else:
            msg = 'Strategy is not active.  Click to activate it for trading.'
            ico = 'no'
        button = self.activeButton
        button.setCheckState(Qt.Checked if status else Qt.Unchecked)
        button.setIcon(QIcon(':/images/icons/connect_%s.png' % ico))
        self.activeLabel.setText(msg)

    def on_strategy_loaded(self, value):
        self.loadButton.setCheckState(Qt.Checked if value else Qt.Unchecked)
        if value:
            value = '%s.  Click to unload it.' % value
        else:
            value = 'Strategy unloaded.'
        self.loadLabel.setText(value)

    def on_strategy_loadfail(self, value):
        self.loadButton.setCheckState(Qt.Unchecked)
        value = 'Load failure:  %s.' % value
        self.loadLabel.setText(value)

    @pyqtSignature('int')
    def on_callableType_currentIndexChanged(self, index):
        self.settings.setValue(
            'type', self.callableSelect.callableType.itemData(index))

    def on_callableLocation_textChanged(self, text):
        self.settings.setValue('location', text)

    @pyqtSignature('bool')
    def on_activeButton_clicked(self, checked):
        if not checked and self.strategy.active:
            self.strategy.active = False
        elif not checked and not self.strategy.active:
            pass
        elif checked and self.strategy.active:
            pass
        elif checked and not self.strategy.active:
            settings = Settings()
            settings.beginGroup(Settings.keys.main)
            activate = True
            if settings.value('confirmActivateStrategy', True).toBool():
                activate = QMessageBox.Yes == QMessageBox.question(
                    self, 'Activate Trading Strategy?',
                    'Do you really want to activate your trading strategy?',
                    QMessageBox.Yes|QMessageBox.No)
            if not activate:
                self.activeButton.setCheckState(Qt.Unchecked)
            self.strategy.active = activate

    @pyqtSignature('')
    def on_loadButton_clicked(self, reload=False):
        if self.loadButton.checkState() == Qt.Checked:
            settings = self.settings
            params = dict(
                reload=reload,
                type=str(settings.value('type').toString()),
                location=str(settings.value('location').toString()),
                source=str(settings.value('source').toString()))
            self.strategy.load(params)
        else:
            self.strategy.unload()

    @pyqtSignature('')
    def on_reloadButton_clicked(self):
        self.on_loadButton_clicked(reload=True)

    def on_callableSelect_modified(self):
        if self.loadButton.checkState() == Qt.Checked:
            self.loadLabel.setText(
                'Strategy origin modified.'
                'Click Reload to re-read it into memory.')
