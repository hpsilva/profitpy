#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

import logging

from PyQt4.QtCore import (Qt, QModelIndex, QVariant, pyqtSignature,
                          QAbstractTableModel, )

from PyQt4.QtGui import (QFrame, QIcon, QMessageBox, QPushButton,
                         QItemDelegate, QStandardItem,
                         QStandardItemModel, )

from profit.lib.core import SessionHandler, Settings, Signals
from profit.workbench.widgets.ui_strategydisplay import Ui_StrategyDisplay


class StrategyControlModel(QAbstractTableModel):
    columnTitles = ['Active', 'Name', 'File', 'Trades']
    typeDecoders = {
        'int':lambda v:v.toInt()[0],
        'QString':lambda v:v.toString(),
        'double':lambda v:v.toDouble()[0],
        'bool':lambda v:v.toBool(),
        }
    typeDecoders[None] = typeDecoders['QString']

    typeEncoders = {
        0 : lambda v:(2 if v else 0),
        1 : lambda v:v,
        }
    typeEncoders[None] = typeEncoders[1]

    def __init__(self, session, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.session = session
        self.stratigies = [
            [True, 'Test One', '/home/troy/foo.strategy', 34, ],
            [False, 'Test Two', '/var/run/...', 13, ]
            ]
        if session:
            session.registerMeta(self)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        column = index.column()
        flags = QAbstractTableModel.flags(self, index)
        #Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if column == 0:
            flags = flags | \
                    Qt.ItemIsUserCheckable | \
                    Qt.ItemIsEditable
        if column == 1:
            flags =  flags | Qt.ItemIsEditable
        if column == 2:
            flags = flags | Qt.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            print '## setData WARN', index.isValid(), role
            return False
        row, col = index.row(), index.column()
        cf = self.typeDecoders.get(value.typeName(), self.typeDecoders[None])
        nv = cf(value)
        cv = self.stratigies[row][col]
        self.stratigies[row][col] = nv
        return (cv == nv)

    def data(self, index, role):
        """ Framework hook to determine data stored at index for given role.

        @param index QModelIndex instance
        @param role Qt.DisplayRole flags
        @return QVariant instance
        """
        if not index.isValid():
            return QVariant()
# col 0 row 0 role 6 FontRole
# col 0 row 0 role 7 TextAlignmentRole
# col 0 row 0 role 9 TextColorRole
# col 0 row 0 role 10 CheckStateRole
# col 0 row 0 role 1 DecorationRole
# col 0 row 0 role 0 DisplayRole
# col 0 row 0 role 8 BackgroundRole

        #print '##:: ', index.row(), index.column(), role
        #if role not in (Qt.DisplayRole, Qt.CheckStateRole, Qt.EditRole):
        #    return QVariant()
        row, col, sts = index.row(), index.column(), self.stratigies
        val = QVariant()
        cell = sts[row][col]
        encoder = self.typeEncoders.get(col, self.typeEncoders[None])
        cell = encoder(cell)
        if col == 0:
            #print '# col', col, 'row', row, 'role', role
            if role in (Qt.DecorationRole, Qt.CheckStateRole):
                val = QVariant(cell)
        elif col == 1:
            if role == Qt.DisplayRole:
                val = QVariant(cell)
        elif col == 2:
            if role == Qt.DisplayRole:
                val = QVariant(cell)
        elif col == 3:
            if role == Qt.DisplayRole:
                val = QVariant(cell)
        return val

    def headerData(self, section, orientation, role):
        """ Framework hook to determine header data.

        @param section integer specifying header (e.g., column number)
        @param orientation Qt.Orientation value
        @param role Qt.DisplayRole flags
        @return QVariant instance
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.columnTitles[section])
        return QVariant()

    def rowCount(self, parent=None):
        """ Framework hook to determine data model row count.

        @param parent ignored
        @return number of rows (message count)
        """
        return len(self.stratigies)

    def columnCount(self, parent=None):
        """ Framework hook to determine data model column count.

        @param parent ignored
        @return number of columns (see columnTitles)
        """
        return len(self.columnTitles)


class StrategyDisplay(QFrame, Ui_StrategyDisplay, SessionHandler):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.inactiveIcon = QIcon(':/images/icons/connect_no.png')
        self.activeIcon = QIcon(':/images/icons/connect_established.png')
        self.settings = Settings()
        self.settings.beginGroup(Settings.keys.strategy)
        self.setupWidgets()
        self.requestSession()

    def setupWidgets(self):
        getv = self.settings.value
        self.strategyTable.currentChanged = self.on_strategyTable_currentChanged
        #self.connect(edit, Signals.currentIndexChanged, self.on_callableSelect_currentIndexChanged)

    def on_strategyTable_currentChanged(self, index, prev):
        print '### activated', index, prev

    def on_strategyItem_changed(self, item):
        #print '##', item
        if item.column() == 0:
            checked = item.checkState()
            item.setIcon(self.activeIcon if checked else self.inactiveIcon)
            item.setText('active' if checked else 'inactive')

    def setSession(self, session):
        connect = self.connect

        self.strategyModel = strategyModel = StrategyDisplayModel(session)
        strategyTable = self.strategyTable
        strategyTable.setModel(strategyModel)
        connect(strategyModel, Signals.itemChanged, self.on_strategyItem_changed)

        ## tmp init
        import random, string
        def mkItems(i):
            items = [
                QStandardItem('inactive'),
                QStandardItem('item: %s' % i),
                QStandardItem('file://asdf/' + str.join('', [random.choice(string.hexdigits) for i in range(random.randint(10,50))])),
                ]
            for item in items:
                item.setEditable(False)
            items[0].setCheckable(True)
            items[0].setIcon(self.inactiveIcon)
            items[0].setCheckState(Qt.Unchecked)
            #items[1].setText('asdf')
            #items[2].setText('three')
            return items
        for i in range(100):
            items = mkItems(i)
            strategyModel.appendRow(items)

        self.session = session
        self.strategy = strategy = session.strategy
        self.on_strategy_activated(strategy.loader.active)
        self.on_strategy_loaded(strategy.loader.loadMessage)

        connect(strategy.loader, Signals.strategyActivated, self.on_strategy_activated)
        connect(strategy.loader, Signals.strategyLoaded, self.on_strategy_loaded)
        connect(strategy.loader, Signals.strategyLoadFailed, self.on_strategy_loadfail)

        for widget in (self.strategyTable, ):
            hh = widget.horizontalHeader()
            vh = widget.verticalHeader()
            hh.hide()
            vh.hide()
            hh.setResizeMode(hh.Stretch)


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
        if not checked and self.strategy.loader.active:
            self.strategy.loader.active = False
        elif not checked and not self.strategy.loader.active:
            pass
        elif checked and self.strategy.loader.active:
            pass
        elif checked and not self.strategy.loader.active:
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
            self.strategy.loader.active = activate

    @pyqtSignature('')
    def on_loadButton_clicked(self, reload=False):
        if self.loadButton.checkState() == Qt.Checked:
            settings = self.settings
            params = dict(
                reload=reload,
                type=str(settings.value('type').toString()),
                location=str(settings.value('location').toString()),
                source=str(settings.value('source').toString()))
            self.strategy.loader.load(params)
        else:
            self.strategy.loader.unload()

    @pyqtSignature('')
    def on_reloadButton_clicked(self):
        self.on_loadButton_clicked(reload=True)

    def on_callableSelect_modified(self, typeIndex, callType, callLoc, callText, isValid):
        print '####', typeIndex, callType, callLoc, callText, isValid
        logging.debug('CallableSelect modified: %s %s %s', callType, callLoc, callText[0:12])
        if self.loadButton.checkState() == Qt.Checked:
            self.loadLabel.setText(
                'Strategy origin modified.'
                'Click Reload to re-read it into memory.')

    @pyqtSignature('int')
    def on_callableSelect_currentIndexChanged(self, index):
        logging.debug('callableSelect changed')

class StrategyDisplayModel(QStandardItemModel):
    def __init__(self, session, parent=None):
        QStandardItemModel.__init__(self, parent)
        self.session = session
