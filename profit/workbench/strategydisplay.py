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
from profit.workbench.widgets.ui_strategydisplay import Ui_StrategyDisplay


class StrategyTableItem(QStandardItem):
    """ Convenience QStandardItem subclass with many init keywords.

    """
    def __init__(self, text='', editable=False, enabled=False, checkable=False,
                 checkState=Qt.Unchecked, icon=None, strategyId=None):
        QStandardItem.__init__(self, text)
        self.setEditable(editable)
        self.setEnabled(enabled)
        self.setCheckable(checkable)
        if checkable:
            self.setCheckState(checkState)
        if icon:
            self.setIcon(icon)
        if strategyId is not None:
            self.setData(QVariant(strategyId), DataRoles.strategyId)


class StrategyDisplayModel(QStandardItemModel):
    """ Model for strategy display table.

    """
    def __init__(self, session, parent=None):
        QStandardItemModel.__init__(self, parent)
        self.session = session
        self.activeIcon = (parent.activeIcon if parent else QIcon())
        self.inactiveIcon = (parent.inactiveIcon if parent else QIcon())

    def appendRowFromData(self, filename, icon):
        """ Create and append row based on model data and method parameters.

        """
        items = self.makeRowItems(self.nextStrategyId(), icon, filename)
        self.appendRow(items)

    def nextStrategyId(self):
        """ Returns next strategy id based on model data.

        """
        items = [self.item(row, 0) for row in range(self.rowCount())]
        ids = [item.data(DataRoles.strategyId).toInt() for item in items]
        ids = [idpair[0] for idpair in ids if idpair[1]] or [0]
        return max(ids) + 1

    def rowToDict(self, row):
        item = self.item(row, 0)
        return {
            'filename':str(self.item(row, 3).text()),
            'strategyId':item.data(DataRoles.strategyId).toInt()[0],
            'active':item.checkState(),
            }

    def encodeRows(self):
        return [self.rowToDict(i) for i in range(self.rowCount())]

    def decodeRows(self, rows):
        for row in rows:
            items = self.makeRowItems(row['strategyId'], self.inactiveIcon, row['filename'])
            self.appendRow(items)

    def makeRowItems(self, strategyId, icon, filename):
        return [
            StrategyTableItem(enabled=True, checkable=True, 
                              checkState=Qt.Unchecked, strategyId=strategyId),
            StrategyTableItem('inactive', icon=icon),
            StrategyTableItem('item: %s' % strategyId),
            StrategyTableItem(filename),
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
        connect = self.connect
        strategyTable = self.strategyTable
        self.strategyModel = strategyModel = StrategyDisplayModel(session, self)
        strategyTable.setModel(strategyModel)
        connect(strategyModel, Signals.itemChanged, 
                self.on_strategyTable_itemChanged)
        connect(strategyTable.selectionModel(), Signals.selectionChanged, 
                self.on_strategyTable_selectionChanged)
        self.session = session
        self.strategy = strategy = session.strategy
        for widget in (self.strategyTable, ):
            hh = widget.horizontalHeader()
            vh = widget.verticalHeader()
            hh.hide()
            vh.hide()
            hh.setResizeMode(hh.ResizeToContents)
        self.readSettings()

    def on_strategyTable_selectionChanged(self, selected, deselected):
        """

        """
        indexes = selected.indexes()
        if indexes:
            ## get the item from the first index (col 0) to determine
            ## if this item is active, where active means checked
            item = self.strategyModel.itemFromIndex(indexes[0])
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
            for col in [1, 2, 3]:
                self.strategyModel.item(item.row(), col).setEnabled(checked)
            self.editButton.setEnabled(not checked)
            self.removeButton.setEnabled(not checked)

    @pyqtSignature('')
    def on_loadButton_clicked(self):
        """

        """
        fn = QFileDialog.getOpenFileName(self, 'Select Strategy File', '')
        if fn:
            self.strategyModel.appendRowFromData(fn, self.inactiveIcon)
            self.saveSettings()

    @pyqtSignature('')
    def on_removeButton_clicked(self):
        """

        """
        indexes = self.strategyTable.selectedIndexes()
        rows = [i.row() for i in indexes if i.isValid()]
        items = [self.strategyModel.item(row, 0) for row in rows]
        for row, item in zip(rows, items):
            strategyId, valid = item.data(DataRoles.strategyId).toInt()
            if valid:
                self.strategyModel.takeRow(row)
        self.strategyTable.clearSelection()
        self.editButton.setEnabled(False)
        self.removeButton.setEnabled(False)
        self.saveSettings()

    def readSettings(self):
        """

        """
        settings = self.settings
        settings.beginGroup(settings.keys.strategy)
        self.strategyModel.decodeRows(settings.valueLoad('strategies', []))
        settings.endGroup()

    def saveSettings(self):
        """

        """
        settings = self.settings
        settings.beginGroup(settings.keys.strategy)
        settings.setValueDump('strategies', self.strategyModel.encodeRows())
        settings.endGroup()
