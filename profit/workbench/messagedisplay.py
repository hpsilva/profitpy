#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from time import ctime

from PyQt4.QtCore import Qt, QVariant, pyqtSignature

from PyQt4.QtGui import (QBrush, QColor, QColorDialog, QIcon, QFrame,
                         QSortFilterProxyModel, QTableWidgetItem, )

from ib.opt.message import messageTypeNames

from profit.lib import defaults
from profit.lib import SessionHandler, SettingsHandler, Slots
from profit.lib.gui import colorIcon
from profit.lib.models.messages import MessagesTableModel
from profit.workbench.widgets.ui_messagedisplay import Ui_MessageDisplay


class MessagesFilter(QSortFilterProxyModel):
    """ MessagesFilter -> proxy model for filtering a message model by types

    """
    def __init__(self, messages, parent=None):
        """ Initializer.

        @param messages sequence of broker messages
        @param parent ancestor object
        """
        QSortFilterProxyModel.__init__(self, parent)
        self.acceptTypes = None
        self.messages = messages

    def filterAcceptsRow(self, row, parent):
        """ Framework hook to filter rows.

        @param row source model rown number
        @param parent QModelIndex instance
        @return True if row should be included in view
        """
        baseClass = QSortFilterProxyModel
        baseAccepts = baseClass.filterAcceptsRow(self, row, parent)
        if self.acceptTypes is None:
            return baseAccepts
        msg = self.messages[row]
        return msg.typeName in self.acceptTypes and baseAccepts

    def includeAll(self):
        """ Sets filter to accept all message types.

        """
        self.acceptTypes = None
        self.reset()

    def includeTypes(self, *names):
        """ Sets filter to include specified message types.

        """
        if self.acceptTypes is None:
            self.acceptTypes = []
        for name in names:
            if name not in self.acceptTypes:
                self.acceptTypes.append(name)
        self.reset()

    def excludeAll(self):
        """ Sets filter to reject all message types.

        """
        self.acceptTypes = []
        self.reset()

    def excludeTypes(self, *names):
        """ Sets filter to reject specified message types.

        """
        if self.acceptTypes is None:
            self.acceptTypes = []
        for name in names:
            if name in self.acceptTypes:
                self.acceptTypes.remove(name)
        self.reset()


class MessageDisplay(QFrame, Ui_MessageDisplay, SessionHandler, SettingsHandler):
    """ MessageDisplay -> table view of session messages with nifty controls

    """
    filterModel = None

    def __init__(self, parent=None):
        """ Initializer.

        @param parent ancestor of this widget
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.brushMap = {}
        self.messageTypeNames = messageTypeNames()
        for widget in (self.messageTable, self.messageDetail):
            widget.verticalHeader().hide()
        ## widget is the messageDetail widget
        horizHeader = widget.horizontalHeader()
        horizHeader.setResizeMode(horizHeader.ResizeToContents)
        settings = self.settings
        settings.beginGroup(settings.keys.messages)
        self.splitter.restoreState(defaults.rightMainSplitterState())
        self.filterBar.setEnabled(False)
        self.setupColors()
        self.requestSession()

    def on_filterEdit_editingFinished(self):
        self.filterModel.setFilterWildcard(self.filterBar.filterEdit.text())

    @pyqtSignature('int')
    def on_allCheck_stateChanged(self, state):
        """ Updates the filter model with all types or those checked.

        @param state 0 if unchecked, 1 if checked
        @return None
        """
        model = self.filterModel
        if state:
            model.includeAll()
        else:
            model.excludeAll()
            model.includeTypes(*self.messageTypeDisplay.selectedTypes())

    @pyqtSignature('')
    def on_checkNoneButton_clicked(self):
        """ Updates the filter model to exclude all message types.

        """
        self.filterModel.excludeAll()

    @pyqtSignature('')
    def on_checkAllButton_clicked(self):
        """ Updates the filter model to include all message types.

        """
        self.filterModel.includeAll()

    def on_typesList_itemChanged(self, item):
        model = self.filterModel
        if model is None:
            return
        call = model.includeTypes if item.checkState() else model.excludeTypes
        call(str(item.text()))

    def on_typesList_itemDoubleClicked(self, item):
        """ Displays a dialog for selecting the color of a message type.

        """
        currentColor = QColor(item.data(Qt.DecorationRole))
        color = QColorDialog.getColor(currentColor, self)
        if color.isValid():
            item.setData(Qt.DecorationRole, QVariant(color))
            item.setIcon(colorIcon(color))
            self.brushMap[str(item.text())] = itemBrush = QBrush(color)
            self.messagesModel.reset()
            self.settings.setValue('%s/color' % item.text(), color)
            messageDetail = self.messageDetail
            typeItem = messageDetail.item(1, 1) # yuk
            if typeItem.text() == item.text():
                for row in range(messageDetail.rowCount()):
                    nameItem = messageDetail.item(row, 0)
                    valueItem = messageDetail.item(row, 1)
                    nameItem.setForeground(itemBrush)
                    valueItem.setForeground(itemBrush)

    def setupColors(self):
        """ Configures the color highlight button.

        @return None
        """
        getValue = self.settings.value
        defaultColor = QColor(0,0,0)
        for name in self.messageTypeNames:
            self.brushMap[name] = getValue('%s/color' % name, defaultColor)
        items = self.messageTypeDisplay.listItems()
        for item in items:
            color = QColor(self.brushMap[str(item.text())])
            item.setData(Qt.DecorationRole, QVariant(color))
            item.setIcon(colorIcon(color))

    def setSession(self, session):
        """ Configures this instance for a session.

        @param session Session instance
        @return None
        """
        self.session = session
        self.messagesModel = MessagesTableModel(session, self.brushMap, self)
        self.filterModel = MessagesFilter(session.messagesBare, self)
        self.filterModel.setFilterKeyColumn(3)
        self.filterModel.setSourceModel(self.messagesModel)
        self.messageTable.setModel(self.filterModel)
        if 0:
            session.registerAll(self.messageTable, Slots.scrollToBottom)

    def on_messageTable_clicked(self, index):
        """ Displays the message keys and values.

        @param index QModelIndex instance; filterModel index, not messageModel.
        @return None
        """
        row = index.row()
        messageIndex, validIndex = index.sibling(row, 0).data().toInt()
        if not validIndex:
            return
        row = messageIndex
        mtime, message = self.messagesModel.message(messageIndex)
        messageDetail = self.messageDetail
        messageDetail.clearContents()
        typeName = message.typeName
        items = [('index', row), ('type', typeName), ('received', ctime(mtime))]
        items += list(sorted(message.items()))
        messageDetail.setRowCount(len(items))
        itemBrush = QBrush(self.brushMap[typeName])
        for row, (name, value) in enumerate(items):
            nameItem = QTableWidgetItem(name)
            valueItem = QTableWidgetItem(str(value))
            nameItem.setForeground(itemBrush)
            valueItem.setForeground(itemBrush)
            messageDetail.setItem(row, 0, nameItem)
            messageDetail.setItem(row, 1, valueItem)

    def on_syncSource_stateChanged(self, state):
        state = bool(state)
        self.messagesModel.setSync(state)
        if state:
            self.filterBar.filterEdit.setText('')
            self.on_filterEdit_editingFinished()
        self.filterBar.setEnabled(not state)

