#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import (Qt, QModelIndex, QVariant, pyqtSignature,
                          QAbstractTableModel, )

from PyQt4.QtGui import (QFrame, QIcon, QMessageBox, QPushButton,
                         QItemDelegate, QStandardItem,
                         QStandardItemModel, QFileDialog, )

from profit.lib import defaults, logging
from profit.lib.core import SessionHandler, SettingsHandler, Signals, DataRoles
from profit.lib.gui import StandardItem
from profit.workbench.widgets.ui_strategydisplay import Ui_StrategyDisplay


class StrategyDisplayModel(QStandardItemModel):
    """ Model for strategy display table.

    """
    labels = ['Active', 'Status', 'File', ]

    def __init__(self, session, view, parent=None):
        QStandardItemModel.__init__(self, parent)
        self.session = session
        self.activeIcon = (view.activeIcon if view else QIcon())
        self.inactiveIcon = (view.inactiveIcon if view else QIcon())
        self.setHorizontalHeaderLabels(self.labels)

    def appendRowFromData(self, filename, icon):
        """ Create and append row based on model data and method parameters.

        """
        items = self.makeRowItems(icon, filename)
        self.appendRow(items)

    def rowToDict(self, row):
        """

        """
        return {
            'active':self.item(row, 0).checkState(),
            'filename':str(self.item(row, 2).text()),
        }

    def encodeRows(self):
        """

        """
        return [self.rowToDict(i) for i in range(self.rowCount())]

    def decodeRows(self, rows):
        """

        """
        for row in rows:
            items = self.makeRowItems(self.inactiveIcon,
                                      row['filename'])
            yield items


    def makeRowItems(self, icon, filename):
        """

        """
        return [
            StandardItem(checkable=True, checkState=Qt.Unchecked,
                         enabled=True, alignment=Qt.AlignCenter),
            StandardItem('inactive', icon=icon),
            StandardItem(filename),
        ]


class StrategyDisplay(QFrame, Ui_StrategyDisplay, SessionHandler, SettingsHandler):
    """

    """
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.inactiveIcon = QIcon(':/images/icons/connect_no.png')
        self.activeIcon = QIcon(':/images/icons/connect_established.png')
        self.requestSession()

    def setSession(self, session):
        """

        """
        self.session = session
        connect = self.connect
        try:
            self.strategyModel = model = session.strategy.displayModel
        except (AttributeError, ):
            self.strategyModel = model = session.strategy.displayModel = \
                                 StrategyDisplayModel(session, self)
            self.readSettings()
        view = self.strategyTable
        view.setModel(model)
        view.verticalHeader().hide()
        view.resizeColumnsToContents()
        connect(model, Signals.itemChanged,
                self.on_strategyTable_itemChanged)
        connect(view.selectionModel(), Signals.selectionChanged,
                self.on_strategyTable_selectionChanged)

    def on_strategyTable_selectionChanged(self, selected, deselected):
        """

        """
        try:
            item = self.strategyModel.itemFromIndex(selected.indexes()[0])
        except (IndexError, ):
            pass
        else:
            active = item.checkState()
            self.editButton.setEnabled(not active)
            self.removeButton.setEnabled(not active)

    def on_strategyTable_itemChanged(self, item):
        """

        """
        if item.column() == 0:
            checked = item.checkState()
            other = self.strategyModel.item(item.row(), 1)
            other.setIcon(self.activeIcon if checked else self.inactiveIcon)
            other.setText('active' if checked else 'inactive')
            labels = self.strategyModel.labels
            for col in [labels.index('Status'), labels.index('File'), ]:
                self.strategyModel.item(item.row(), col).setEnabled(checked)
            self.editButton.setEnabled(not checked)
            self.removeButton.setEnabled(not checked)

    @pyqtSignature('bool')
    def on_enableAll_clicked(self, v):
        pass

    @pyqtSignature('bool')
    def on_confirmActivate_clicked(self, v):
        pass

    @pyqtSignature('')
    def on_editButton_clicked(self):
        """

        """
        from profit.strategydesigner.main import StrategyDesigner
        indexes = self.strategyTable.selectedIndexes()
        rows = [i.row() for i in indexes if i.isValid()]
        items = [self.strategyModel.item(row, 0) for row in rows]
        for row, item in zip(rows, items):
            other = self.strategyModel.item(row, 2)
            filename = other.text()
            win = StrategyDesigner(filename=filename, parent=self)
            win.show()
            break ## only first because there should only be one

    @pyqtSignature('')
    def on_loadButton_clicked(self):
        """

        """
        fn = QFileDialog.getOpenFileName(self, 'Select Strategy File', '')
        if fn:
            self.strategyModel.appendRowFromData(fn, self.inactiveIcon)
            self.strategyTable.resizeColumnsToContents()
            self.saveSettings()

    @pyqtSignature('')
    def on_removeButton_clicked(self):
        """

        """
        indexes = self.strategyTable.selectedIndexes()
        rows = set(i.row() for i in indexes if i.isValid())
        for row in reversed(sorted(list(rows))):
            self.strategyModel.takeRow(row)
        self.strategyTable.clearSelection()
        self.editButton.setEnabled(False)
        self.removeButton.setEnabled(False)
        self.saveSettings()

    def readSettings(self):
        """ Load saved strategies and send them to the model.

        """
        settings = self.settings
        settings.beginGroup(settings.keys.strategy)
        model = self.strategyModel
        for row in model.decodeRows(settings.valueLoad('strategies', [])):
            model.appendRow(row)
        settings.endGroup()

    def saveSettings(self):
        """

        """
        settings = self.settings
        settings.beginGroup(settings.keys.strategy)
        settings.setValueDump('strategies', self.strategyModel.encodeRows())
        settings.endGroup()
